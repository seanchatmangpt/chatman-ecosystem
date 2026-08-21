#!/usr/bin/env python3
"""Dual-sensor trailing-window repository activity census.

This module is OBSERVE-only. It reconciles:
1. public owner repositories whose ``pushed_at`` falls in the admitted window;
2. pull requests updated in the same window, grouped by owning repository.

A single sensor is never allowed to imply complete activity recall. Search truncation
or incomplete results fail closed. The emitted receipt binds the exact normalized
observation and can be replay-verified without network access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

API = "https://api.github.com"
SCHEMA = "chatman.portfolio-activity-census/1"
SEARCH_CAP = 1000
GITHUB_EPOCH = date(2008, 1, 1)
MAX_SEARCH_PARTITIONS = 256


class CensusError(RuntimeError):
    """Typed census refusal/failure."""


class SensorClient(Protocol):
    def list_public_owner_repositories(self, owner: str) -> list[dict[str, Any]]: ...
    def search_updated_pull_requests(
        self, owner: str, since: datetime, until: datetime
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...


@dataclass(frozen=True)
class Window:
    since: datetime
    until: datetime

    def __post_init__(self) -> None:
        if self.since.tzinfo is None or self.until.tzinfo is None:
            raise CensusError("window timestamps must be timezone-aware")
        if self.since >= self.until:
            raise CensusError("window since must precede until")

    def contains(self, value: datetime) -> bool:
        return self.since <= value < self.until

    def to_dict(self) -> dict[str, str]:
        return {"since": iso_z(self.since), "until": iso_z(self.until)}


@dataclass(frozen=True)
class SearchSlice:
    """One disjoint creation-date slice of the same updated-PR population."""

    created_since: date
    created_until: date

    def __post_init__(self) -> None:
        if self.created_since > self.created_until:
            raise CensusError("created search slice is inverted")

    def split(self) -> tuple["SearchSlice", "SearchSlice"]:
        if self.created_since == self.created_until:
            raise CensusError(
                "REFUSED[PR_SEARCH_UNSPLITTABLE_DAY_CAP] "
                f"created={self.created_since.isoformat()}"
            )
        span = (self.created_until - self.created_since).days
        midpoint = self.created_since + timedelta(days=span // 2)
        return (
            SearchSlice(self.created_since, midpoint),
            SearchSlice(midpoint + timedelta(days=1), self.created_until),
        )


SearchFetcher = Callable[[SearchSlice | None], tuple[list[dict[str, Any]], int, bool]]


def _pr_search_identity(item: Mapping[str, Any]) -> str:
    item_id = item.get("id")
    if isinstance(item_id, int):
        return f"id:{item_id}"
    node_id = item.get("node_id")
    if isinstance(node_id, str) and node_id:
        return f"node:{node_id}"
    url = item.get("url")
    if isinstance(url, str) and url:
        return f"url:{url}"
    raise CensusError("REFUSED[PR_SEARCH_RESULT_IDENTITY_MISSING]")


def collect_partitioned_pr_search(
    fetch: SearchFetcher,
    *,
    created_floor: date,
    created_ceiling: date,
    search_cap: int = SEARCH_CAP,
    max_partitions: int = MAX_SEARCH_PARTITIONS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect a capped GitHub PR search without weakening completeness checks.

    The cheap broad query remains the default. Only when its reported population is
    above GitHub's 1,000-result search cap do we recursively partition by PR creation
    date. Creation date is orthogonal to the measured ``updated`` window, so every PR
    in the target population belongs to exactly one slice. A single calendar day that
    still exceeds the cap is explicitly refused rather than sampled.
    """

    broad_rows, broad_total, broad_incomplete = fetch(None)
    if broad_incomplete:
        raise CensusError("REFUSED[PR_SEARCH_INCOMPLETE_RESULTS]")
    if broad_total <= search_cap:
        if len(broad_rows) < broad_total:
            raise CensusError(
                "REFUSED[PR_SEARCH_TRUNCATED] "
                f"total_count={broad_total} retrieved={len(broad_rows)}"
            )
        return broad_rows, {
            "reported_total_count": broad_total,
            "retrieved_count": len(broad_rows),
            "search_cap": search_cap,
            "incomplete_results": False,
            "cap_triggered": False,
            "partition_strategy": "none",
            "partition_count": 1,
            "duplicate_count": 0,
            "max_partition_total": broad_total,
        }

    pending = [SearchSlice(created_floor, created_ceiling)]
    accepted: list[tuple[SearchSlice, list[dict[str, Any]], int]] = []
    partition_queries = 0
    max_partition_total = 0
    while pending:
        if partition_queries >= max_partitions:
            raise CensusError(
                "REFUSED[PR_SEARCH_PARTITION_LIMIT] "
                f"limit={max_partitions} pending={len(pending)}"
            )
        current = pending.pop()
        rows, total, incomplete = fetch(current)
        partition_queries += 1
        max_partition_total = max(max_partition_total, total)
        if incomplete:
            raise CensusError(
                "REFUSED[PR_SEARCH_INCOMPLETE_RESULTS] "
                f"created={current.created_since.isoformat()}..{current.created_until.isoformat()}"
            )
        if total > search_cap:
            left, right = current.split()
            pending.append(right)
            pending.append(left)
            continue
        if len(rows) < total:
            raise CensusError(
                "REFUSED[PR_SEARCH_TRUNCATED] "
                f"created={current.created_since.isoformat()}..{current.created_until.isoformat()} "
                f"total_count={total} retrieved={len(rows)}"
            )
        accepted.append((current, rows, total))

    accepted.sort(key=lambda entry: entry[0].created_since)
    unique: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for _, rows, _ in accepted:
        for row in rows:
            identity = _pr_search_identity(row)
            if identity in unique:
                duplicate_count += 1
                continue
            unique[identity] = row

    return list(unique.values()), {
        "reported_total_count": broad_total,
        "retrieved_count": len(unique),
        "search_cap": search_cap,
        "incomplete_results": False,
        "cap_triggered": True,
        "partition_strategy": "created_date_recursive",
        "partition_count": partition_queries,
        "leaf_partition_count": len(accepted),
        "duplicate_count": duplicate_count,
        "max_partition_total": max_partition_total,
    }


class GitHubClient:
    """Minimal read-only GitHub client. No mutation endpoints are reachable."""

    def __init__(self, token: str | None = None, api_url: str = API, timeout: float = 30.0) -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str) -> Any:
        url = path if path.startswith("http") else f"{self.api_url}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "chatman-ecosystem-activity-census/1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise CensusError(f"GitHub HTTP {exc.code} for {url}: {body[:400]}") from exc
        except urllib.error.URLError as exc:
            raise CensusError(f"GitHub transport failed for {url}: {exc.reason}") from exc

    def list_public_owner_repositories(self, owner: str) -> list[dict[str, Any]]:
        quoted = urllib.parse.quote(owner, safe="")
        rows: list[dict[str, Any]] = []
        for page in range(1, 101):
            payload = self._request(
                f"/users/{quoted}/repos?type=owner&sort=full_name&direction=asc&per_page=100&page={page}"
            )
            if not isinstance(payload, list):
                raise CensusError("repository sensor returned non-list payload")
            if not payload:
                return rows
            rows.extend(x for x in payload if isinstance(x, dict))
        raise CensusError("REFUSED[REPOSITORY_PAGINATION_UNBOUNDED]")

    def _fetch_pr_search_slice(
        self,
        *,
        owner: str,
        since: datetime,
        until: datetime,
        search_slice: SearchSlice | None,
    ) -> tuple[list[dict[str, Any]], int, bool]:
        # GitHub issue-search dates are day-granularity. Exact updated timestamps are
        # reapplied locally after retrieval; creation-date slices are disjoint days.
        q_parts = [
            f"user:{owner}",
            "is:pr",
            f"updated:{since.date().isoformat()}..{until.date().isoformat()}",
        ]
        if search_slice is not None:
            q_parts.append(
                "created:"
                f"{search_slice.created_since.isoformat()}..{search_slice.created_until.isoformat()}"
            )
        q = " ".join(q_parts)
        rows: list[dict[str, Any]] = []
        total_count: int | None = None
        incomplete = False
        for page in range(1, 11):
            params = urllib.parse.urlencode(
                {"q": q, "per_page": 100, "page": page, "sort": "created", "order": "asc"}
            )
            payload = self._request(f"/search/issues?{params}")
            if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
                raise CensusError("PR sensor returned invalid search payload")
            if total_count is None:
                total_count = int(payload.get("total_count", 0))
            incomplete = incomplete or bool(payload.get("incomplete_results", False))
            items = [x for x in payload["items"] if isinstance(x, dict)]
            rows.extend(items)
            if not items or len(rows) >= min(total_count, SEARCH_CAP):
                break
        return rows, total_count or 0, incomplete

    def search_updated_pull_requests(
        self, owner: str, since: datetime, until: datetime
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        return collect_partitioned_pr_search(
            lambda search_slice: self._fetch_pr_search_slice(
                owner=owner,
                since=since,
                until=until,
                search_slice=search_slice,
            ),
            created_floor=GITHUB_EPOCH,
            created_ceiling=until.date(),
        )


def parse_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CensusError(f"invalid timestamp: {value}") from exc
    if result.tzinfo is None:
        raise CensusError(f"timestamp lacks timezone: {value}")
    return result.astimezone(timezone.utc)


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def repository_from_pr(item: Mapping[str, Any], owner: str) -> str | None:
    repository_url = item.get("repository_url")
    if not isinstance(repository_url, str) or "/repos/" not in repository_url:
        return None
    repo = repository_url.split("/repos/", 1)[1]
    if not repo.startswith(f"{owner}/"):
        return None
    return repo


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def build_census(
    client: SensorClient,
    *,
    owner: str,
    window: Window,
) -> dict[str, Any]:
    repos = client.list_public_owner_repositories(owner)
    pushed_active: set[str] = set()
    malformed_repo_rows = 0
    for repo in repos:
        full_name = repo.get("full_name")
        pushed_at = repo.get("pushed_at")
        if not isinstance(full_name, str) or not full_name.startswith(f"{owner}/"):
            malformed_repo_rows += 1
            continue
        if not isinstance(pushed_at, str):
            continue
        try:
            pushed_time = parse_time(pushed_at)
        except CensusError:
            malformed_repo_rows += 1
            continue
        if window.contains(pushed_time):
            pushed_active.add(full_name)

    prs, pr_evidence = client.search_updated_pull_requests(owner, window.since, window.until)
    pr_active: set[str] = set()
    pr_updates_in_window = 0
    malformed_pr_rows = 0
    for pr in prs:
        updated_at = pr.get("updated_at")
        repo = repository_from_pr(pr, owner)
        if not isinstance(updated_at, str) or repo is None:
            malformed_pr_rows += 1
            continue
        try:
            updated_time = parse_time(updated_at)
        except CensusError:
            malformed_pr_rows += 1
            continue
        if window.contains(updated_time):
            pr_updates_in_window += 1
            pr_active.add(repo)

    union = pushed_active | pr_active
    push_only = pushed_active - pr_active
    pr_only = pr_active - pushed_active
    intersection = pushed_active & pr_active

    observation = {
        "schema": SCHEMA,
        "owner": owner,
        "window": window.to_dict(),
        "sensors": {
            "public_owner_repository_push": {
                "observed_repository_rows": len(repos),
                "active_repository_count": len(pushed_active),
                "active_repositories": sorted(pushed_active),
                "malformed_rows": malformed_repo_rows,
                "scope": "public owner repositories only",
            },
            "updated_pull_request": {
                **pr_evidence,
                "updates_in_exact_window": pr_updates_in_window,
                "active_repository_count": len(pr_active),
                "active_repositories": sorted(pr_active),
                "malformed_rows": malformed_pr_rows,
            },
        },
        "reconciliation": {
            "union_repository_count": len(union),
            "union_repositories": sorted(union),
            "intersection_count": len(intersection),
            "intersection_repositories": sorted(intersection),
            "push_only_count": len(push_only),
            "push_only_repositories": sorted(push_only),
            "pr_only_count": len(pr_only),
            "pr_only_repositories": sorted(pr_only),
            "single_sensor_complete_activity_claim": False,
        },
        "standing": "PARTIAL_ALIVE",
        "claim_ceiling": "OBSERVED_PUBLIC_ACTIVITY_UNION",
        "exclusions": [
            "private repositories not visible through the public owner sensor",
            "issue-only activity",
            "workflow-only activity without a push or PR update",
            "local/unpushed work",
            "complete materiality classification",
        ],
    }
    digest = hashlib.sha256(canonical_bytes(observation)).hexdigest()
    return {
        **observation,
        "receipt": {
            "algorithm": "sha256",
            "observation_digest": digest,
            "replay": "recompute canonical JSON without receipt and require exact digest equality",
        },
    }


def verify_receipt(census: Mapping[str, Any]) -> bool:
    receipt = census.get("receipt")
    if not isinstance(receipt, Mapping):
        return False
    expected = receipt.get("observation_digest")
    if not isinstance(expected, str):
        return False
    observation = dict(census)
    observation.pop("receipt", None)
    actual = hashlib.sha256(canonical_bytes(observation)).hexdigest()
    return actual == expected


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="seanchatmangpt")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--until")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output", type=Path, default=Path(".artifacts/activity-census/census.json"))
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)

    if args.replay:
        payload = json.loads(args.replay.read_text(encoding="utf-8"))
        if verify_receipt(payload):
            print(f"ALIVE:ACTIVITY_CENSUS_REPLAY digest={payload['receipt']['observation_digest']}")
            return 0
        print("REFUSED[ACTIVITY_CENSUS_REPLAY_MISMATCH]", file=sys.stderr)
        return 2

    if args.days <= 0:
        print("REFUSED[INVALID_WINDOW_DAYS]", file=sys.stderr)
        return 2

    until = parse_time(args.until) if args.until else datetime.now(timezone.utc)
    window = Window(since=until - timedelta(days=args.days), until=until)
    token = os.getenv(args.token_env) or None
    try:
        census = build_census(GitHubClient(token=token), owner=args.owner, window=window)
    except CensusError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json(args.output, census)
    print(
        "PARTIAL_ALIVE:ACTIVITY_CENSUS "
        f"union={census['reconciliation']['union_repository_count']} "
        f"push_only={census['reconciliation']['push_only_count']} "
        f"pr_only={census['reconciliation']['pr_only_count']} "
        f"digest={census['receipt']['observation_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
