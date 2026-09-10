#!/usr/bin/env python3
"""Validate the Frontier Release Factory control contract and bounded receipts."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "catalog" / "frontier-release-factory.toml"

REQUIRED_INVARIANTS = {
    "source_release_is_observation",
    "working_backwards_release_is_candidate",
    "llm_output_is_candidate_only",
    "capability_is_not_authority",
    "select_construct_do_separate",
    "zero_unreceipted_actuation",
    "generated_projection_is_not_canonical",
    "exact_subject_required",
    "earned_claim_requires_alive_evidence",
    "replay_never_reactuates_do",
    "reuse_compose_extend_before_invent",
}

REQUIRED_REFUSALS = {
    "SOURCE_RELEASE_AS_AUTHORITY",
    "LLM_GRANTED_DO_AUTHORITY",
    "WORKING_BACKWARDS_AS_EARNED",
    "UNRECEIPTED_REPOSITORY_CREATION",
    "UNRECEIPTED_PUBLICATION",
    "GENERATED_ARTIFACT_EDITED_AS_SOURCE",
    "EARNED_CLAIM_WITHOUT_ALIVE_EVIDENCE",
    "REPLAY_REACTUATED_DO",
    "SILENT_SUBJECT_SUBSTITUTION",
}

REQUIRED_ROLES = {
    "control-plane",
    "manufacturing-packs",
    "product-surface",
    "process-runtime",
    "process-intelligence",
    "deterministic-manufacturer",
    "ash-manufacturer",
}

EXPECTED_STAGES = [
    "observe",
    "extract",
    "fence",
    "invert",
    "specify",
    "create-repository",
    "manufacture",
    "verify",
    "publish",
]

REQUIRED_RECEIPT_FIELDS = {
    "source_identity",
    "source_digest",
    "opportunity_identity",
    "target_repository",
    "implementation_subject",
    "verifier_identities",
    "execution_receipts",
    "replay_references",
    "claim_standing",
}


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if manifest.get("schema") != "chatman.frontier-release-factory.v1":
        errors.append("invalid schema")

    invariants = manifest.get("invariants", {})
    missing = sorted(name for name in REQUIRED_INVARIANTS if invariants.get(name) is not True)
    if missing:
        errors.append(f"required invariants not true: {', '.join(missing)}")

    refusals = set(invariants.get("terminal_refusals", []))
    missing_refusals = sorted(REQUIRED_REFUSALS - refusals)
    if missing_refusals:
        errors.append(f"missing terminal refusals: {', '.join(missing_refusals)}")

    receipt_fields = set(manifest.get("receipt", {}).get("required_fields", []))
    if receipt_fields != REQUIRED_RECEIPT_FIELDS:
        errors.append("receipt.required_fields must equal the v1 receipt contract")

    roles = manifest.get("repository_role", [])
    role_ids = [role.get("id") for role in roles]
    if set(role_ids) != REQUIRED_ROLES or len(role_ids) != len(set(role_ids)):
        errors.append("repository roles must be complete and unique")
    if any(not role.get("repository") or not role.get("responsibility") for role in roles):
        errors.append("every repository role requires repository and responsibility")

    stages = sorted(manifest.get("stage", []), key=lambda stage: stage.get("ordinal", -1))
    stage_ids = [stage.get("id") for stage in stages]
    if stage_ids != EXPECTED_STAGES:
        errors.append("stage graph must equal the ordered v1 lifecycle")

    for stage in stages:
        if stage.get("class") == "DO":
            if stage.get("broker_required") is not True:
                errors.append(f"DO stage {stage.get('id')} must require broker")
            if stage.get("receipt_required") is not True:
                errors.append(f"DO stage {stage.get('id')} must require receipt")

    do_stage_ids = {stage.get("id") for stage in stages if stage.get("class") == "DO"}
    if do_stage_ids != {"create-repository", "publish"}:
        errors.append("v1 DO stages must be exactly create-repository and publish")

    routes = manifest.get("route", [])
    llm_routes = [route for route in routes if route.get("route") == "LLM"]
    if len(llm_routes) != 1:
        errors.append("exactly one LLM route is required")
    else:
        llm = llm_routes[0]
        if llm.get("problem_class") != "semantic-unknown":
            errors.append("LLM route must be semantic-unknown only")
        if llm.get("candidate_only") is not True or llm.get("authority") != "NONE":
            errors.append("LLM route must be candidate-only with no authority")

    route_by_class = {route.get("problem_class"): route for route in routes}
    for problem_class in ("repository-creation", "publication"):
        route = route_by_class.get(problem_class, {})
        if route.get("authority") != "DO" or "BRCE" not in str(route.get("route", "")):
            errors.append(f"{problem_class} must route to DO through BRCE")

    contract = manifest.get("release_contract", {})
    if contract.get("working_backwards_status") != "CANDIDATE":
        errors.append("working-backwards release must remain CANDIDATE")
    if contract.get("earned_status_requires") != "ALIVE":
        errors.append("earned release must require ALIVE evidence")

    return errors


def evaluate_receipt(manifest: dict[str, Any], receipt: dict[str, Any]) -> str:
    violations = set(receipt.get("violations", []))
    terminal = set(manifest["invariants"]["terminal_refusals"])
    hit = sorted(violations & terminal)
    if hit:
        return f"REFUSED:{hit[0]}"

    for field in manifest["receipt"]["required_fields"]:
        if field not in receipt or receipt[field] in (None, "", [], {}):
            return "PARTIAL_ALIVE"

    claim_standing = receipt.get("claim_standing")
    if not isinstance(claim_standing, dict) or not claim_standing:
        return "PARTIAL_ALIVE"
    if any(value != "ALIVE" for value in claim_standing.values()):
        return "PARTIAL_ALIVE"

    if receipt.get("replay_reactuated_do") is True:
        return "REFUSED:REPLAY_REACTUATED_DO"

    return "ALIVE"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(f"REFUSED:MANIFEST_INVALID:{error}")
        return 2

    if args.receipt is None:
        print("MANIFEST_ALIVE")
        return 0

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    standing = evaluate_receipt(manifest, receipt)
    print(standing)
    if standing == "ALIVE":
        return 0
    if standing.startswith("REFUSED:"):
        return 2
    return 3


if __name__ == "__main__":
    sys.exit(main())
