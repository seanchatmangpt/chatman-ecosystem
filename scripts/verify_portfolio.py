#!/usr/bin/env python3
"""Verify total fleet scope policy and candidate/admitted identity separation."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DISPOSITION_KEYS = {
    "crown": "CROWN",
    "required": "REQUIRED",
    "adapter": "ADAPTER",
    "bench_gym": "BENCH_GYM",
    "source_archaeology": "SOURCE_ARCHAEOLOGY",
    "explicit_out_of_release": "OUT_OF_RELEASE",
}
ALLOWED_SCOPE_STANDINGS = {"UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"}


def load(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def classify(policy: dict[str, Any], repository: str) -> str:
    fleet = policy["fleet"]
    if repository == fleet["composition_root"]:
        return "CROWN"
    dispositions = policy["dispositions"]
    for key, disposition in DISPOSITION_KEYS.items():
        if repository in dispositions.get(key, []):
            return disposition
    return fleet["default_disposition"]


def validate_pagination_evidence(fleet: dict[str, Any]) -> list[dict[str, str]]:
    """Validate an observed count against its pagination receipt without freezing a historical count."""
    findings: list[dict[str, str]] = []

    def add(code: str, subject: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "detail": detail})

    count = fleet.get("observed_owned_repository_count")
    pages = fleet.get("nonempty_pages")
    page_size = fleet.get("page_size")
    next_page_empty = fleet.get("next_page_empty")

    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        add("FLEET_OBSERVED_COUNT_INVALID", "fleet.observed_owned_repository_count", str(count))
    if not isinstance(pages, int) or isinstance(pages, bool) or pages < 1:
        add("FLEET_NONEMPTY_PAGES_INVALID", "fleet.nonempty_pages", str(pages))
    if not isinstance(page_size, int) or isinstance(page_size, bool) or page_size < 1:
        add("FLEET_PAGE_SIZE_INVALID", "fleet.page_size", str(page_size))
    if next_page_empty is not True:
        add("FLEET_PAGINATION_TERMINATOR_INVALID", "fleet.next_page_empty", str(next_page_empty))

    if findings:
        return findings

    assert isinstance(count, int)
    assert isinstance(pages, int)
    assert isinstance(page_size, int)
    minimum = (pages - 1) * page_size + 1
    maximum = pages * page_size
    if not minimum <= count <= maximum:
        add(
            "FLEET_OBSERVED_COUNT_PAGINATION_MISMATCH",
            "fleet",
            f"count={count} requires {minimum}..{maximum} for pages={pages} page_size={page_size}",
        )
    return findings


def validate(policy: dict[str, Any], manifest: dict[str, Any], candidates: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    fleet = policy.get("fleet", {})
    roadmap = policy.get("roadmap", {})
    dispositions = policy.get("dispositions", {})

    def add(code: str, subject: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "detail": detail})

    if fleet.get("owner") != "seanchatmangpt":
        add("FLEET_OWNER_INVALID", "fleet.owner", str(fleet.get("owner")))
    findings.extend(validate_pagination_evidence(fleet))
    if fleet.get("default_disposition") != "OUT_OF_RELEASE" or fleet.get("default_release_blocking") is not False:
        add("FLEET_DEFAULT_NOT_FAIL_SAFE", "fleet", "unclassified repositories must be non-blocking OUT_OF_RELEASE")

    required_roadmaps = {"CROWN", "REQUIRED", "ADAPTER", "BENCH_GYM", "SOURCE_ARCHAEOLOGY", "OUT_OF_RELEASE"}
    missing_roadmaps = sorted(required_roadmaps - roadmap.keys())
    if missing_roadmaps:
        add("FLEET_ROADMAP_MISSING", "roadmap", ",".join(missing_roadmaps))

    seen: dict[str, str] = {}
    for key, disposition in DISPOSITION_KEYS.items():
        repos = dispositions.get(key, [])
        if not isinstance(repos, list) or not all(isinstance(repo, str) for repo in repos):
            add("FLEET_DISPOSITION_LIST_INVALID", key, "must be an array of repository coordinates")
            continue
        for repo in repos:
            if not repo.startswith("seanchatmangpt/"):
                add("FLEET_REPOSITORY_OWNER_INVALID", repo, key)
            if repo in seen:
                add("FLEET_REPOSITORY_MULTI_DISPOSITION", repo, f"{seen[repo]} and {disposition}")
            seen[repo] = disposition

    manifest_components = manifest.get("components", [])
    expected = {component["repository"]: component["disposition"] for component in manifest_components if component.get("required")}
    actual_release = {
        repo: disposition
        for repo, disposition in seen.items()
        if disposition in {"CROWN", "REQUIRED"}
    }
    if expected != actual_release:
        add("FLEET_RELEASE_CLOSURE_MISMATCH", "dispositions", f"manifest={sorted(expected.items())} fleet={sorted(actual_release.items())}")

    root = fleet.get("composition_root")
    if not isinstance(root, str) or classify(policy, root) != "CROWN":
        add("FLEET_COMPOSITION_ROOT_INVALID", str(root), "composition root must classify as CROWN")

    by_component = {component["id"]: component for component in manifest_components}
    candidate_rows = candidates.get("candidates", [])
    seen_candidate_components: set[str] = set()
    for candidate in candidate_rows:
        component_id = candidate.get("component")
        if component_id in seen_candidate_components:
            add("CANDIDATE_DUPLICATE_COMPONENT", str(component_id), "one current candidate per component")
            continue
        seen_candidate_components.add(component_id)
        admitted = by_component.get(component_id)
        if admitted is None:
            add("CANDIDATE_COMPONENT_NOT_ADMITTED", str(component_id), "candidate component must exist in release manifest")
            continue
        if candidate.get("repository") != admitted.get("repository"):
            add("CANDIDATE_REPOSITORY_MISMATCH", str(component_id), str(candidate.get("repository")))
        if candidate.get("admitted_sha") != admitted.get("sha"):
            add("CANDIDATE_ADMITTED_SHA_MISMATCH", str(component_id), f"manifest={admitted.get('sha')} candidate={candidate.get('admitted_sha')}")
        candidate_sha = candidate.get("candidate_sha")
        if not isinstance(candidate_sha, str) or not SHA_RE.fullmatch(candidate_sha):
            add("CANDIDATE_SHA_INVALID", str(component_id), str(candidate_sha))
        if candidate_sha == admitted.get("sha"):
            add("CANDIDATE_NOT_DISTINCT", str(component_id), "candidate SHA must remain distinct until promotion")
        if candidate.get("scope_standing") not in ALLOWED_SCOPE_STANDINGS:
            add("CANDIDATE_SCOPE_STANDING_INVALID", str(component_id), str(candidate.get("scope_standing")))
        if candidate.get("release_standing") != "UNKNOWN":
            add("CANDIDATE_RELEASE_STANDING_OVERCLAIM", str(component_id), str(candidate.get("release_standing")))
        if candidate.get("exact_head_ci") != "SUCCESS":
            add("CANDIDATE_EXACT_HEAD_CI_NOT_SUCCESS", str(component_id), str(candidate.get("exact_head_ci")))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fleet", type=Path, default=Path("release/v26.9.1/fleet-policy.toml"))
    parser.add_argument("--manifest", type=Path, default=Path("release/v26.9.1/manifest.toml"))
    parser.add_argument("--candidates", type=Path, default=Path("release/v26.9.1/candidates.toml"))
    args = parser.parse_args(argv)
    policy = load(args.fleet)
    manifest = load(args.manifest)
    candidates = load(args.candidates)
    findings = validate(policy, manifest, candidates)
    report = {
        "release": manifest.get("release", {}).get("version"),
        "observed_owned_repository_count": policy.get("fleet", {}).get("observed_owned_repository_count"),
        "default_disposition": policy.get("fleet", {}).get("default_disposition"),
        "explicit_non_default_repositories": sum(len(policy.get("dispositions", {}).get(key, [])) for key in DISPOSITION_KEYS),
        "candidate_count": len(candidates.get("candidates", [])),
        "standing": "ALIVE" if not findings else "BLOCKED",
        "findings": findings,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not findings else 2


if __name__ == "__main__":
    sys.exit(main())
