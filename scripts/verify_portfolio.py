#!/usr/bin/env python3
"""Verify fleet scope plus typed release-candidate / observation separation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
RECEIPT_SCHEMA = "chatman.portfolio-verification/2"
DISPOSITION_KEYS = {
    "crown": "CROWN",
    "required": "REQUIRED",
    "adapter": "ADAPTER",
    "bench_gym": "BENCH_GYM",
    "source_archaeology": "SOURCE_ARCHAEOLOGY",
    "explicit_out_of_release": "OUT_OF_RELEASE",
}
ALLOWED_SCOPE_STANDINGS = {"UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"}


class PortfolioRefusal(ValueError):
    pass


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


def row_kind(row: dict[str, Any]) -> str:
    """Classify legacy ledger rows without promoting observations into candidates.

    Candidate rows carry a concrete candidate_sha. Rows that only record a locally
    observed head intentionally remain OBSERVATION rows. An explicit kind, when
    present, must agree with the structural shape.
    """
    explicit = row.get("kind")
    inferred = "CANDIDATE" if "candidate_sha" in row else "OBSERVATION"
    if explicit is None:
        return inferred
    if explicit not in {"CANDIDATE", "OBSERVATION"}:
        raise PortfolioRefusal(f"REFUSED[LEDGER_KIND_INVALID] {explicit!r}")
    if explicit != inferred:
        raise PortfolioRefusal(
            f"REFUSED[LEDGER_KIND_SHAPE_MISMATCH] kind={explicit} inferred={inferred}"
        )
    return explicit


def validate_pagination_evidence(fleet: dict[str, Any]) -> list[dict[str, str]]:
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
    minimum = (pages - 1) * page_size + 1
    maximum = pages * page_size
    if not minimum <= count <= maximum:
        add("FLEET_OBSERVED_COUNT_PAGINATION_MISMATCH", "fleet", f"count={count} requires {minimum}..{maximum} for pages={pages} page_size={page_size}")
    return findings


def validate(policy: dict[str, Any], manifest: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, str]]:
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
    actual_release = {repo: disposition for repo, disposition in seen.items() if disposition in {"CROWN", "REQUIRED"}}
    if expected != actual_release:
        add("FLEET_RELEASE_CLOSURE_MISMATCH", "dispositions", f"manifest={sorted(expected.items())} fleet={sorted(actual_release.items())}")

    root = fleet.get("composition_root")
    if not isinstance(root, str) or classify(policy, root) != "CROWN":
        add("FLEET_COMPOSITION_ROOT_INVALID", str(root), "composition root must classify as CROWN")

    by_component = {component["id"]: component for component in manifest_components}
    rows = ledger.get("candidates", [])
    seen_components: set[str] = set()
    for row in rows:
        component_id = row.get("component")
        if component_id in seen_components:
            add("CANDIDATE_DUPLICATE_COMPONENT", str(component_id), "one ledger row per component")
            continue
        seen_components.add(component_id)
        admitted = by_component.get(component_id)
        if admitted is None:
            add("CANDIDATE_COMPONENT_NOT_ADMITTED", str(component_id), "ledger component must exist in release manifest")
            continue
        if row.get("repository") != admitted.get("repository"):
            add("CANDIDATE_REPOSITORY_MISMATCH", str(component_id), str(row.get("repository")))
        if row.get("scope_standing") not in ALLOWED_SCOPE_STANDINGS:
            add("CANDIDATE_SCOPE_STANDING_INVALID", str(component_id), str(row.get("scope_standing")))
        if row.get("release_standing") != "UNKNOWN":
            add("CANDIDATE_RELEASE_STANDING_OVERCLAIM", str(component_id), str(row.get("release_standing")))

        try:
            kind = row_kind(row)
        except PortfolioRefusal as exc:
            add("LEDGER_KIND_REFUSED", str(component_id), str(exc))
            continue

        if kind == "OBSERVATION":
            observed_sha = row.get("admitted_sha")
            if not isinstance(observed_sha, str) or not SHA_RE.fullmatch(observed_sha):
                add("OBSERVATION_SHA_INVALID", str(component_id), str(observed_sha))
            # Observation rows intentionally carry no candidate admission or CI claim.
            if "exact_head_ci" in row:
                add("OBSERVATION_CI_AUTHORITY_INVALID", str(component_id), str(row.get("exact_head_ci")))
            continue

        if row.get("admitted_sha") != admitted.get("sha"):
            add("CANDIDATE_ADMITTED_SHA_MISMATCH", str(component_id), f"manifest={admitted.get('sha')} candidate={row.get('admitted_sha')}")
        candidate_sha = row.get("candidate_sha")
        if not isinstance(candidate_sha, str) or not SHA_RE.fullmatch(candidate_sha):
            add("CANDIDATE_SHA_INVALID", str(component_id), str(candidate_sha))
        if candidate_sha == admitted.get("sha"):
            add("CANDIDATE_NOT_DISTINCT", str(component_id), "candidate SHA must remain distinct until promotion")
        if row.get("exact_head_ci") != "SUCCESS":
            add("CANDIDATE_EXACT_HEAD_CI_NOT_SUCCESS", str(component_id), str(row.get("exact_head_ci")))

    return findings


def build_report(policy: dict[str, Any], manifest: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    findings = validate(policy, manifest, ledger)
    rows = ledger.get("candidates", [])
    candidate_count = 0
    observation_count = 0
    for row in rows:
        try:
            kind = row_kind(row)
        except PortfolioRefusal:
            continue
        candidate_count += kind == "CANDIDATE"
        observation_count += kind == "OBSERVATION"
    return {
        "schema": RECEIPT_SCHEMA,
        "release": manifest.get("release", {}).get("version"),
        "observed_owned_repository_count": policy.get("fleet", {}).get("observed_owned_repository_count"),
        "default_disposition": policy.get("fleet", {}).get("default_disposition"),
        "explicit_non_default_repositories": sum(len(policy.get("dispositions", {}).get(key, [])) for key in DISPOSITION_KEYS),
        "candidate_count": candidate_count,
        "observation_count": observation_count,
        "standing": "ALIVE" if not findings else "BLOCKED",
        "findings": findings,
    }


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def manufacture_receipt(report: dict[str, Any]) -> dict[str, Any]:
    body = dict(report)
    return {**body, "sha256": hashlib.sha256(_canonical(body)).hexdigest()}


def replay_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_SCHEMA]")
    digest = receipt.get("sha256")
    if not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
        raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_DIGEST_INVALID]")
    body = {key: value for key, value in receipt.items() if key != "sha256"}
    if hashlib.sha256(_canonical(body)).hexdigest() != digest:
        raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_TAMPERED]")
    if receipt.get("standing") != "ALIVE" or receipt.get("findings") != []:
        raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_NOT_ALIVE]")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fleet", type=Path, default=Path("release/v26.9.1/fleet-policy.toml"))
    parser.add_argument("--manifest", type=Path, default=Path("release/v26.9.1/manifest.toml"))
    parser.add_argument("--candidates", type=Path, default=Path("release/v26.9.1/candidates.toml"))
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.replay:
            receipt = json.loads(args.replay.read_text(encoding="utf-8"))
            replay_receipt(receipt)
            print(json.dumps(receipt, sort_keys=True))
            return 0
        report = build_report(load(args.fleet), load(args.manifest), load(args.candidates))
        receipt = manufacture_receipt(report)
        if args.receipt:
            args.receipt.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0 if not report["findings"] else 2
    except (OSError, json.JSONDecodeError, PortfolioRefusal) as exc:
        print(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
