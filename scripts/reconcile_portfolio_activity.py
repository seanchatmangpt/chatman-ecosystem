#!/usr/bin/env python3
"""Dual-sensor trailing-window repository activity census.

OBSERVE-only measurement instrument. It reconciles:
1. public owner repositories whose ``pushed_at`` falls in the admitted window;
2. pull requests updated in the same window, grouped by owning repository.

The PR sensor recursively partitions timestamp ranges whenever GitHub's search API
reports more than its 1,000-result accessible window. Each admitted partition is
fully paginated, the union is deduplicated by stable issue identity, and the exact
half-open time window is re-applied locally before standing is computed.
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

API = "https://api.github.com"
SCHEMA = "chatman.portfolio-activity-census/2"
SEARCH_CAP = 1000
PER_PAGE = 100


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


def floor_second(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(microsecond=0)


def inclusive_search_bounds(since: datetime, until: datetime) -> tuple[datetime, datetime]:
    """Convert exact [since, until) to a superset of whole-second search bounds."""
    start = floor_second(since)
    end_floor = floor_second(until)
    if until.astimezone(timezone.utc).microsecond:
        end = end_floor
    else:
        end = end_floor - timedelta(seconds=1)
    if end < start:
        end = start
    return start, end


def iso_z(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def repository_from_pr(item: Mapping[str, Any], owner: str) -> str | None:
    repository_url = item.get("repository_url")
    if not isinstance(repository_url, str) or "/repos/" not in repository_url:
        return None
    repo = repository_url.split("/repos/", 1)[1]
    if not repo.startswith(f"{owner}/"):
        return None
    return repo


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def stable_pr_key(item: Mapping[str, Any]) -> str:
    node_id = item.get("node_id")
    if isinstance(node_id, str) and node_id:
        return f"node:{node_id}"
    item_id = item.get("id")
    if isinstance(item_id, int):
        return f"id:{item_id}"
    url = item.get("url")
    if isinstance(url, str) and url:
        return f"url:{url}"
    raise CensusError("REFUSED[PR_ROW_IDENTITY_MISSING]")


class GitHubClient:
    """Minimal read-only GitHub client. No mutation endpoints are reachable."""

    def __init__(
        self, token: str | None = None, api_url: str = API, timeout: float = 30.0
    ) -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str) -> Any:
        url = path if path.startswith("http") else f"{self.api_url}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "chatman-ecosystem-activity-census/2",
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
            raise CensusError(
                f"GitHub HTTP {exc.code} for {url}: {body[:400]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise CensusError(
                f"GitHub transport failed for {url}: {exc.reason}"
            ) from exc

    def list_public_owner_repositories(self, owner: str) -> list[dict[str, Any]]:
        quoted = urllib.parse.quote(owner, safe="")
        rows: list[dict[str, Any]] = []
        for page in range(1, 101):
            payload = self._request(
                f"/users/{quoted}/repos?type=owner&sort=full_name&direction=asc"
                f"&per_page=100&page={page}"
            )
            if not isinstance(payload, list):
                raise CensusError("repository sensor returned non-list payload")
            if not payload:
                return rows
            rows.extend(x for x in payload if isinstance(x, dict))
        raise CensusError("REFUSED[REPOSITORY_PAGINATION_UNBOUNDED]")

    @staticmethod
    def _query(owner: str, start: datetime, end: datetime) -> str:
        return f"user:{owner} is:pr updated:{iso_z(start)}..{iso_z(end)}"

    def _search_page(
        self, owner: str, start: datetime, end: datetime, page: int
    ) -> dict[str, Any]:
        params = urllib.parse.urlencode(
            {
                "q": self._query(owner, start, end),
                "per_page": PER_PAGE,
                "page": page,
                "sort": "updated",
                "order": "asc",
            }
        )
        payload = self._request(f"/search/issues?{params}")
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise CensusError("PR sensor returned invalid search payload")
        return payload

    def _search_partition(
        self,
        owner: str,
        start: datetime,
        end: datetime,
        *,
        depth: int = 0,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        first = self._search_page(owner, start, end, 1)
        total = int(first.get("total_count", 0))
        if bool(first.get("incomplete_results", False)):
            raise CensusError("REFUSED[PR_SEARCH_INCOMPLETE_RESULTS]")

        if total > SEARCH_CAP:
            if start >= end:
                raise CensusError(
                    "REFUSED[PR_SEARCH_PARTITION_CAP] "
                    f"second={iso_z(start)} total_count={total}"
                )
            span_seconds = int((end - start).total_seconds())
            midpoint = start + timedelta(seconds=span_seconds // 2)
            right_start = midpoint + timedelta(seconds=1)
            left_rows, left_segments = self._search_partition(
                owner, start, midpoint, depth=depth + 1
            )
            right_rows, right_segments = self._search_partition(
                owner, right_start, end, depth=depth + 1
            )
            return left_rows + right_rows, left_segments + right_segments

        items = [x for x in first["items"] if isinstance(x, dict)]
        pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        for page in range(2, pages + 1):
            payload = self._search_page(owner, start, end, page)
            if bool(payload.get("incomplete_results", False)):
                raise CensusError("REFUSED[PR_SEARCH_INCOMPLETE_RESULTS]")
            if int(payload.get("total_count", 0)) != total:
                raise CensusError(
                    "REFUSED[PR_SEARCH_PARTITION_DRIFT] "
                    f"range={iso_z(start)}..{iso_z(end)}"
                )
            items.extend(x for x in payload["items"] if isinstance(x, dict))

        if len(items) != total:
            raise CensusError(
                "REFUSED[PR_SEARCH_TRUNCATED] "
                f"range={iso_z(start)}..{iso_z(end)} "
                f"total_count={total} retrieved={len(items)}"
            )
        segment = {
            "since_inclusive": iso_z(start),
            "until_inclusive": iso_z(end),
            "reported_total_count": total,
            "retrieved_count": len(items),
            "depth": depth,
        }
        return items, [segment]

    def search_updated_pull_requests(
        self, owner: str, since: datetime, until: datetime
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        start, end = inclusive_search_bounds(since, until)
        root = self._search_page(owner, start, end, 1)
        root_total = int(root.get("total_count", 0))
        if bool(root.get("incomplete_results", False)):
            raise CensusError("REFUSED[PR_SEARCH_INCOMPLETE_RESULTS]")

        if root_total <= SEARCH_CAP:
            rows, segments = self._search_partition(owner, start, end)
        else:
            if start >= end:
                raise CensusError(
                    "REFUSED[PR_SEARCH_PARTITION_CAP] "
                    f"second={iso_z(start)} total_count={root_total}"
                )
            span_seconds = int((end - start).total_seconds())
            midpoint = start + timedelta(seconds=span_seconds // 2)
            rows_left, segments_left = self._search_partition(owner, start, midpoint)
            rows_right, segments_right = self._search_partition(
                owner, midpoint + timedelta(seconds=1), end
            )
            rows = rows_left + rows_right
            segments = segments_left + segments_right

        unique: dict[str, dict[str, Any]] = {}
        for row in rows:
            unique.setdefault(stable_pr_key(row), row)

        evidence = {
            "root_reported_total_count": root_total,
            "retrieved_count": len(rows),
            "retrieved_unique_count": len(unique),
            "deduplicated_count": len(rows) - len(unique),
            "search_cap": SEARCH_CAP,
            "partition_strategy": "recursive-bisection-by-updated-second",
            "partition_count": len(segments),
            "max_partition_total": max(
                (int(s["reported_total_count"]) for s in segments), default=0
            ),
            "incomplete_results": False,
            "partitions": segments,
        }
        return list(unique.values()), evidence


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

    prs, pr_evidence = client.search_updated_pull_requests(
        owner, window.since, window.until
    )
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
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="seanchatmangpt")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--until")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".artifacts/activity-census/census.json"),
    )
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)

    if args.replay:
        payload = json.loads(args.replay.read_text(encoding="utf-8"))
        if verify_receipt(payload):
            print(
                "ALIVE:ACTIVITY_CENSUS_REPLAY "
                f"digest={payload['receipt']['observation_digest']}"
            )
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
        census = build_census(
            GitHubClient(token=token), owner=args.owner, window=window
        )
    except CensusError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json(args.output, census)
    sensor = census["sensors"]["updated_pull_request"]
    print(
        "PARTIAL_ALIVE:ACTIVITY_CENSUS "
        f"union={census['reconciliation']['union_repository_count']} "
        f"push_only={census['reconciliation']['push_only_count']} "
        f"pr_only={census['reconciliation']['pr_only_count']} "
        f"pr_updates={sensor['updates_in_exact_window']} "
        f"partitions={sensor.get('partition_count', 0)} "
        f"digest={census['receipt']['observation_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
