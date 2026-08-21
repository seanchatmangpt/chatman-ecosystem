#!/usr/bin/env python3
"""Reconcile GitHub Actions outcomes for an admitted repository activity census.

OBSERVE-only measurement instrument. It consumes a replay-valid activity census,
queries workflow runs for each repository in that admitted union over the same
exact half-open window, and emits a deterministic receipt. It never promotes CI
coverage to repository correctness and never treats workflow existence as success.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

SCHEMA = "chatman.ci-outcome-census/1"
ACTIVITY_SCHEMA_PREFIX = "chatman.portfolio-activity-census/"
API = "https://api.github.com"
PER_PAGE = 100
MAX_PAGES = 100


class CIOutcomeError(RuntimeError):
    """Typed CI outcome census refusal/failure."""


class ActionsClient(Protocol):
    def list_workflow_runs(self, repo: str, since: datetime, until: datetime) -> list[dict[str, Any]]: ...


def parse_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CIOutcomeError(f"invalid timestamp: {value}") from exc
    if result.tzinfo is None:
        raise CIOutcomeError(f"timestamp lacks timezone: {value}")
    return result.astimezone(timezone.utc)


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def verify_embedded_receipt(payload: Mapping[str, Any]) -> bool:
    receipt = payload.get("receipt")
    if not isinstance(receipt, Mapping):
        return False
    expected = receipt.get("observation_digest")
    if not isinstance(expected, str):
        return False
    observation = dict(payload)
    observation.pop("receipt", None)
    actual = hashlib.sha256(canonical_bytes(observation)).hexdigest()
    return actual == expected


def verify_receipt(payload: Mapping[str, Any]) -> bool:
    return verify_embedded_receipt(payload)


class GitHubActionsClient:
    """Minimal read-only GitHub Actions client."""

    def __init__(self, token: str | None = None, api_url: str = API, timeout: float = 30.0) -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str) -> Any:
        url = path if path.startswith("http") else f"{self.api_url}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "chatman-ecosystem-ci-outcome-census/1",
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
            raise CIOutcomeError(f"GitHub HTTP {exc.code} for {url}: {body[:400]}") from exc
        except urllib.error.URLError as exc:
            raise CIOutcomeError(f"GitHub transport failed for {url}: {exc.reason}") from exc

    def list_workflow_runs(self, repo: str, since: datetime, until: datetime) -> list[dict[str, Any]]:
        if "/" not in repo:
            raise CIOutcomeError(f"REFUSED[REPOSITORY_IDENTITY_INVALID] repo={repo}")
        owner, name = repo.split("/", 1)
        created = f"{iso_z(since)}..{iso_z(until)}"
        rows: list[dict[str, Any]] = []
        reported_total: int | None = None
        for page in range(1, MAX_PAGES + 1):
            params = urllib.parse.urlencode({"created": created, "per_page": PER_PAGE, "page": page})
            payload = self._request(
                f"/repos/{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(name, safe='')}/actions/runs?{params}"
            )
            if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
                raise CIOutcomeError(f"REFUSED[CI_RUN_PAYLOAD_INVALID] repo={repo}")
            total = int(payload.get("total_count", 0))
            if reported_total is None:
                reported_total = total
            elif total != reported_total:
                raise CIOutcomeError(f"REFUSED[CI_RUN_COUNT_DRIFT] repo={repo} expected={reported_total} observed={total}")
            page_rows = [x for x in payload["workflow_runs"] if isinstance(x, dict)]
            rows.extend(page_rows)
            if len(rows) >= total or not page_rows:
                break
        else:
            raise CIOutcomeError(f"REFUSED[CI_RUN_PAGINATION_UNBOUNDED] repo={repo}")
        if reported_total is None:
            return []
        if len(rows) < reported_total:
            raise CIOutcomeError(f"REFUSED[CI_RUN_TRUNCATED] repo={repo} total_count={reported_total} retrieved={len(rows)}")
        return rows


def stable_run_key(run: Mapping[str, Any]) -> str:
    run_id = run.get("id")
    if isinstance(run_id, int):
        return f"id:{run_id}"
    node_id = run.get("node_id")
    if isinstance(node_id, str) and node_id:
        return f"node:{node_id}"
    raise CIOutcomeError("REFUSED[CI_RUN_IDENTITY_MISSING]")


def build_ci_census(client: ActionsClient, activity: Mapping[str, Any]) -> dict[str, Any]:
    schema = activity.get("schema")
    if not isinstance(schema, str) or not schema.startswith(ACTIVITY_SCHEMA_PREFIX):
        raise CIOutcomeError("REFUSED[ACTIVITY_CENSUS_SCHEMA]")
    if not verify_embedded_receipt(activity):
        raise CIOutcomeError("REFUSED[ACTIVITY_CENSUS_RECEIPT]")

    owner = activity.get("owner")
    window = activity.get("window")
    reconciliation = activity.get("reconciliation")
    if not isinstance(owner, str) or not isinstance(window, Mapping) or not isinstance(reconciliation, Mapping):
        raise CIOutcomeError("REFUSED[ACTIVITY_CENSUS_SHAPE]")
    since_raw, until_raw = window.get("since"), window.get("until")
    repos_raw = reconciliation.get("union_repositories")
    if not isinstance(since_raw, str) or not isinstance(until_raw, str) or not isinstance(repos_raw, list):
        raise CIOutcomeError("REFUSED[ACTIVITY_CENSUS_SHAPE]")
    since, until = parse_time(since_raw), parse_time(until_raw)
    if since >= until:
        raise CIOutcomeError("REFUSED[ACTIVITY_WINDOW_INVALID]")

    repos: list[str] = []
    for repo in repos_raw:
        if not isinstance(repo, str) or not repo.startswith(f"{owner}/"):
            raise CIOutcomeError(f"REFUSED[ACTIVITY_REPOSITORY_OUT_OF_SCOPE] repo={repo!r}")
        repos.append(repo)
    if len(set(repos)) != len(repos):
        raise CIOutcomeError("REFUSED[ACTIVITY_REPOSITORY_DUPLICATE]")

    per_repo: list[dict[str, Any]] = []
    total_runs = completed_runs = pending_runs = 0
    conclusion_counts: dict[str, int] = {}
    repos_with_runs = repos_without_runs = repos_with_failure = 0

    for repo in sorted(repos):
        raw_runs = client.list_workflow_runs(repo, since, until)
        unique: dict[str, dict[str, Any]] = {}
        duplicate_count = 0
        for run in raw_runs:
            key = stable_run_key(run)
            if key in unique:
                duplicate_count += 1
            else:
                unique[key] = run

        admitted: list[dict[str, Any]] = []
        malformed = 0
        for run in unique.values():
            created_raw = run.get("created_at")
            if not isinstance(created_raw, str):
                malformed += 1
                continue
            try:
                created_at = parse_time(created_raw)
            except CIOutcomeError:
                malformed += 1
                continue
            if not (since <= created_at < until):
                continue
            status = run.get("status") if isinstance(run.get("status"), str) else "unknown"
            conclusion = run.get("conclusion") if isinstance(run.get("conclusion"), str) else None
            admitted.append({
                "id": run.get("id"),
                "name": run.get("name") if isinstance(run.get("name"), str) else None,
                "event": run.get("event") if isinstance(run.get("event"), str) else None,
                "head_sha": run.get("head_sha") if isinstance(run.get("head_sha"), str) else None,
                "created_at": iso_z(created_at),
                "status": status,
                "conclusion": conclusion,
            })

        admitted.sort(key=lambda x: (x["created_at"], str(x["id"])))
        repo_completed = sum(1 for r in admitted if r["status"] == "completed")
        repo_pending = len(admitted) - repo_completed
        repo_failures = sum(1 for r in admitted if r["conclusion"] in {"failure", "timed_out", "startup_failure", "action_required"})
        for r in admitted:
            key = r["conclusion"] if r["conclusion"] is not None else f"STATUS:{r['status']}"
            conclusion_counts[key] = conclusion_counts.get(key, 0) + 1
        total_runs += len(admitted)
        completed_runs += repo_completed
        pending_runs += repo_pending
        if admitted:
            repos_with_runs += 1
        else:
            repos_without_runs += 1
        if repo_failures:
            repos_with_failure += 1
        per_repo.append({
            "repository": repo,
            "run_count": len(admitted),
            "completed_count": repo_completed,
            "pending_count": repo_pending,
            "failure_like_count": repo_failures,
            "duplicate_rows": duplicate_count,
            "malformed_rows": malformed,
            "latest_run": admitted[-1] if admitted else None,
            "runs": admitted,
        })

    repo_count = len(repos)
    observation = {
        "schema": SCHEMA,
        "owner": owner,
        "window": {"since": iso_z(since), "until": iso_z(until)},
        "activity_subject": {
            "schema": schema,
            "observation_digest": activity["receipt"]["observation_digest"],
            "union_repository_count": repo_count,
        },
        "summary": {
            "admitted_repository_count": repo_count,
            "repositories_with_observed_ci_runs": repos_with_runs,
            "repositories_without_observed_ci_runs": repos_without_runs,
            "repositories_with_failure_like_outcomes": repos_with_failure,
            "observed_run_count": total_runs,
            "completed_run_count": completed_runs,
            "pending_run_count": pending_runs,
            "conclusion_counts": dict(sorted(conclusion_counts.items())),
            "ci_observation_coverage": None if repo_count == 0 else repos_with_runs / repo_count,
        },
        "repositories": per_repo,
        "standing": "PARTIAL_ALIVE",
        "claim_ceiling": "OBSERVED_GITHUB_ACTIONS_RUNS_FOR_ADMITTED_ACTIVITY_UNION",
        "exclusions": [
            "non-GitHub CI providers",
            "local-only build/test execution",
            "workflow runs outside the admitted activity window",
            "repository correctness inferred from workflow success",
            "required-check semantics not declared by repository policy",
            "private repositories absent from the upstream activity census",
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


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activity-census", type=Path)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.replay:
            payload = json.loads(args.replay.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not verify_receipt(payload):
                raise CIOutcomeError("REFUSED[CI_CENSUS_RECEIPT]")
            print(json.dumps({"standing": "ALIVE", "replay": "MATCH", "receipt": payload["receipt"]}, sort_keys=True))
            return 0
        if not args.activity_census or not args.output:
            parser.error("--activity-census and --output are required unless --replay is used")
        activity = json.loads(args.activity_census.read_text(encoding="utf-8"))
        if not isinstance(activity, dict):
            raise CIOutcomeError("REFUSED[ACTIVITY_CENSUS_SHAPE]")
        token = os.environ.get(args.token_env) if args.token_env else None
        result = build_ci_census(GitHubActionsClient(token=token), activity)
        write_json(args.output, result)
        print(json.dumps(result["summary"], sort_keys=True))
        return 0
    except (CIOutcomeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
