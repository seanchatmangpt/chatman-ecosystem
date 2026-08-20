#!/usr/bin/env python3
"""Fail-closed verifier for the cross-repository pending-branch composition bundle."""
from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "release" / "v26.9.1" / "pending-branches.toml"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_REPOSITORIES = {
    "autofde-lab": "seanchatmangpt/autofde-lab",
    "gymact": "seanchatmangpt/gymact",
    "mfw": "seanchatmangpt/mfw",
}
ALLOWED_ROLES = {"INTEGRATION", "SOURCE"}


class Refusal(RuntimeError):
    pass


def refuse(code: str) -> None:
    raise Refusal(code)


def load_bundle(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate(data: dict) -> dict:
    bundle = data.get("bundle")
    repositories = data.get("repository")
    branches = data.get("branch")
    if not isinstance(bundle, dict):
        refuse("REFUSED:BUNDLE_HEADER_MISSING")
    if not isinstance(repositories, list) or not isinstance(branches, list):
        refuse("REFUSED:BUNDLE_COLLECTION_MISSING")

    if bundle.get("schema") != "chatman.pending-branch-bundle/1":
        refuse("REFUSED:BUNDLE_SCHEMA")
    if bundle.get("root_repository") != "seanchatmangpt/chatman-ecosystem":
        refuse("REFUSED:ROOT_REPOSITORY")
    if bundle.get("claim_ceiling") != "OBSERVED_PENDING_BRANCH_GRAPH":
        refuse("REFUSED:CLAIM_CEILING")
    for key in ("do_authority", "merge_authority", "release_authority"):
        if bundle.get(key) is not False:
            refuse(f"REFUSED:AUTHORITY_ESCALATION:{key}")

    if bundle.get("repository_count") != len(repositories):
        refuse("REFUSED:REPOSITORY_COUNT_DRIFT")
    if bundle.get("branch_count") != len(branches):
        refuse("REFUSED:BRANCH_COUNT_DRIFT")

    repo_by_name: dict[str, dict] = {}
    repo_ids: set[str] = set()
    for item in repositories:
        repo_id = item.get("id")
        repo_name = item.get("repository")
        if repo_id not in EXPECTED_REPOSITORIES or EXPECTED_REPOSITORIES[repo_id] != repo_name:
            refuse("REFUSED:REPOSITORY_SET_DRIFT")
        if repo_id in repo_ids or repo_name in repo_by_name:
            refuse("REFUSED:DUPLICATE_REPOSITORY")
        repo_ids.add(repo_id)
        repo_by_name[repo_name] = item
        if not SHA40.fullmatch(str(item.get("integration_sha", ""))):
            refuse(f"REFUSED:INVALID_INTEGRATION_SHA:{repo_name}")
        if not isinstance(item.get("integration_pr"), int) or item["integration_pr"] <= 0:
            refuse(f"REFUSED:INVALID_INTEGRATION_PR:{repo_name}")
        if not isinstance(item.get("integration_ref"), str) or not item["integration_ref"].strip():
            refuse(f"REFUSED:INVALID_INTEGRATION_REF:{repo_name}")

    if repo_ids != set(EXPECTED_REPOSITORIES):
        refuse("REFUSED:REPOSITORY_SET_INCOMPLETE")

    seen_prs: set[tuple[str, int]] = set()
    seen_refs: set[tuple[str, str]] = set()
    integration_matches: dict[str, int] = {repo: 0 for repo in repo_by_name}
    per_repo_counts: dict[str, int] = {repo: 0 for repo in repo_by_name}

    for item in branches:
        repo = item.get("repository")
        if repo not in repo_by_name:
            refuse(f"REFUSED:UNDECLARED_REPOSITORY:{repo}")
        pr = item.get("pr")
        ref = item.get("ref")
        sha = item.get("sha")
        base_sha = item.get("base_sha")
        role = item.get("role")
        if not isinstance(pr, int) or pr <= 0:
            refuse(f"REFUSED:INVALID_PR:{repo}")
        if not isinstance(ref, str) or not ref.strip():
            refuse(f"REFUSED:INVALID_REF:{repo}#{pr}")
        if not SHA40.fullmatch(str(sha)) or not SHA40.fullmatch(str(base_sha)):
            refuse(f"REFUSED:INVALID_SHA:{repo}#{pr}")
        if role not in ALLOWED_ROLES:
            refuse(f"REFUSED:INVALID_ROLE:{repo}#{pr}")
        if item.get("state") != "OPEN":
            refuse(f"REFUSED:NON_PENDING_BRANCH:{repo}#{pr}")
        if not isinstance(item.get("draft"), bool) or not isinstance(item.get("mergeable"), bool):
            refuse(f"REFUSED:INVALID_PR_FLAGS:{repo}#{pr}")

        pr_key = (repo, pr)
        ref_key = (repo, ref)
        if pr_key in seen_prs:
            refuse(f"REFUSED:DUPLICATE_PR:{repo}#{pr}")
        if ref_key in seen_refs:
            refuse(f"REFUSED:DUPLICATE_REF:{repo}:{ref}")
        seen_prs.add(pr_key)
        seen_refs.add(ref_key)
        per_repo_counts[repo] += 1

        integration = repo_by_name[repo]
        exact_integration = (
            pr == integration["integration_pr"]
            and ref == integration["integration_ref"]
            and sha == integration["integration_sha"]
        )
        if role == "INTEGRATION":
            if not exact_integration:
                refuse(f"REFUSED:INTEGRATION_IDENTITY_DRIFT:{repo}#{pr}")
            integration_matches[repo] += 1
        elif exact_integration:
            refuse(f"REFUSED:INTEGRATION_ROLE_DRIFT:{repo}#{pr}")

    for repo, count in integration_matches.items():
        if count != 1:
            refuse(f"REFUSED:INTEGRATION_CARDINALITY:{repo}:{count}")
        if per_repo_counts[repo] == 0:
            refuse(f"REFUSED:EMPTY_REPOSITORY_BRANCH_SET:{repo}")

    return {
        "schema": bundle["schema"],
        "standing": "OBSERVED",
        "claim_ceiling": bundle["claim_ceiling"],
        "repository_count": len(repositories),
        "branch_count": len(branches),
        "integration_count": sum(integration_matches.values()),
        "per_repository": dict(sorted(per_repo_counts.items())),
        "merge_authority": False,
        "do_authority": False,
        "release_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        receipt = validate(load_bundle(args.bundle))
    except (OSError, tomllib.TOMLDecodeError, Refusal) as exc:
        print(str(exc))
        return 2
    if args.json:
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "PENDING_BRANCH_BUNDLE_OBSERVED "
            f"repositories={receipt['repository_count']} branches={receipt['branch_count']} "
            f"integrations={receipt['integration_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
