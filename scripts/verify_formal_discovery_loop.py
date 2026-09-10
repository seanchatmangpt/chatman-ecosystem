#!/usr/bin/env python3
"""Validate the canonical formal-discovery-loop contract and evaluate receipts.

The verifier checks architecture closure. It does not prove a mathematical theorem and
must not be used to transfer standing from a manifest to an unexecuted discovery run.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "catalog" / "formal-discovery-loop.toml"

EXPECTED_STANDING = {
    "UNKNOWN",
    "PARTIAL_ALIVE",
    "ALIVE",
    "BLOCKED",
    "BUILD_BROKEN",
    "UNSUPPORTED",
}

REQUIRED_PRINCIPLES = {
    "ontology_before_search",
    "dfcm_preserves_reversible_options",
    "hdit_preserves_decision_sufficient_information",
    "hddl_decomposes_search",
    "known_classes_route_to_specialized_machinery",
    "ggen_manufactures_projections",
    "llm_is_unknown_frontier_candidate_producer_only",
    "generated_artifacts_are_not_canonical",
    "lean_is_admission_kernel",
    "lake_is_reproducible_build_and_dependency_graph",
    "axiom_footprint_is_receipted",
    "negative_controls_are_required",
    "mfact_certifies_standing",
    "admitted_delta_returns_to_ontology",
    "zero_unreceipted_actuation",
}

REQUIRED_RECEIPT_FIELDS = {
    "exact_subject",
    "ontology_digest",
    "search_plan_digest",
    "candidate_digest",
    "lean_toolchain",
    "lake_manifest_digest",
    "axiom_audit_digest",
    "negative_control_receipts",
    "manufacturer_identities",
    "verifier_identities",
    "replay_references",
    "admitted_delta_digest",
    "standing",
}

REQUIRED_TERMINAL_REFUSALS = {
    "LLM_GRANTED_DO_AUTHORITY",
    "GENERATED_ARTIFACT_EDITED_AS_SOURCE",
    "LEAN_ADMISSION_BYPASSED",
    "UNAUDITED_AXIOM_PROMOTED",
    "NEGATIVE_CONTROL_REMOVED",
    "STALE_TOOLCHAIN_STANDING_TRANSFER",
    "UNRECEIPTED_ONTOLOGY_MUTATION",
    "TRANSCRIPT_PROMOTED_TO_CANONICAL_KNOWLEDGE",
}

REQUIRED_STAGE_ORDER = [
    "reconstruct-ontology",
    "preserve-option-surface",
    "decompose-search",
    "project-decision-information",
    "route-known-leaves",
    "explore-unknown-frontier",
    "manufacture-formal-candidates",
    "lean-admission",
    "lake-build-replay",
    "audit-axioms-and-falsifiers",
    "certify-standing",
    "close-ontology-loop",
]

REQUIRED_ROUTES = {
    "ontology-query": "RDF/SPARQL/SHACL",
    "algebra": "CAS",
    "constraint": "SAT/SMT/CP",
    "optimization": "OR",
    "hierarchical-planning": "HDDL/HTN",
    "formal-proof": "Lean4",
    "formal-build-replay": "Lake",
    "projection-manufacture": "ggen",
    "formal-certification": "mfact",
    "semantic-unknown": "LLM",
}


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _has_cycle(stages: dict[str, dict[str, Any]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(stage_id: str) -> bool:
        if stage_id in visiting:
            return True
        if stage_id in visited:
            return False
        visiting.add(stage_id)
        for dependency in stages[stage_id].get("requires", []):
            if dependency in stages and visit(dependency):
                return True
        visiting.remove(stage_id)
        visited.add(stage_id)
        return False

    return any(visit(stage_id) for stage_id in stages)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if manifest.get("schema") != "chateco.formal-discovery-loop.v1":
        errors.append("schema must be chateco.formal-discovery-loop.v1")
    if manifest.get("canonical_state") != "ontology":
        errors.append("canonical_state must be ontology")
    if manifest.get("feedback_target") != "reconstruct-ontology":
        errors.append("feedback_target must close into reconstruct-ontology")

    allowed = set(manifest.get("standing_vocabulary", {}).get("allowed", []))
    if allowed != EXPECTED_STANDING:
        errors.append("standing vocabulary must equal the bounded protocol vocabulary")

    principles = manifest.get("principles", {})
    missing_principles = sorted(
        name for name in REQUIRED_PRINCIPLES if principles.get(name) is not True
    )
    if missing_principles:
        errors.append(f"required principles not true: {', '.join(missing_principles)}")

    receipt_fields = set(manifest.get("receipt", {}).get("required_fields", []))
    missing_fields = sorted(REQUIRED_RECEIPT_FIELDS - receipt_fields)
    if missing_fields:
        errors.append(f"missing receipt fields: {', '.join(missing_fields)}")

    terminal_refusals = set(manifest.get("refusals", {}).get("terminal", []))
    missing_refusals = sorted(REQUIRED_TERMINAL_REFUSALS - terminal_refusals)
    if missing_refusals:
        errors.append(f"missing terminal refusals: {', '.join(missing_refusals)}")

    routes = manifest.get("route", [])
    by_class: dict[str, dict[str, Any]] = {}
    for index, route in enumerate(routes):
        problem_class = route.get("problem_class")
        if not isinstance(problem_class, str) or not problem_class:
            errors.append(f"route[{index}] requires a non-empty problem_class")
            continue
        if problem_class in by_class:
            errors.append(f"duplicate route: {problem_class}")
            continue
        by_class[problem_class] = route

    for problem_class, machine in REQUIRED_ROUTES.items():
        route = by_class.get(problem_class)
        if route is None:
            errors.append(f"missing route: {problem_class}")
            continue
        if route.get("machine") != machine:
            errors.append(f"route {problem_class} must use {machine}")
        if problem_class == "semantic-unknown":
            if route.get("llm_allowed") is not True or route.get("candidate_only") is not True:
                errors.append("semantic-unknown LLM route must be candidate_only")
        elif route.get("llm_allowed") is not False:
            errors.append(f"known route {problem_class} must not require an LLM")

    stage_list = manifest.get("stage", [])
    stages: dict[str, dict[str, Any]] = {}
    actual_order: list[str] = []
    for index, stage in enumerate(stage_list):
        stage_id = stage.get("id")
        if not isinstance(stage_id, str) or not stage_id:
            errors.append(f"stage[{index}] requires a non-empty id")
            continue
        if stage_id in stages:
            errors.append(f"duplicate stage id: {stage_id}")
            continue
        if stage.get("half") not in {"discovery", "admission"}:
            errors.append(f"stage {stage_id} half must be discovery or admission")
        if stage.get("class") not in {"OBSERVE", "SELECT", "CONSTRUCT"}:
            errors.append(f"stage {stage_id} class must not imply DO authority")
        stages[stage_id] = stage
        actual_order.append(stage_id)

    if actual_order != REQUIRED_STAGE_ORDER:
        errors.append("stage order must preserve the discovery-to-admission closure")

    for stage_id, stage in stages.items():
        for dependency in stage.get("requires", []):
            if dependency not in stages:
                errors.append(f"stage {stage_id} requires unknown stage {dependency}")

    if _has_cycle(stages):
        errors.append("stage dependency graph must be acyclic; recurrence is via feedback_target")

    if "manufacture-formal-candidates" in stages and "lean-admission" in stages:
        if "manufacture-formal-candidates" not in stages["lean-admission"].get("requires", []):
            errors.append("Lean admission must consume manufactured formal candidates")

    if "certify-standing" in stages and "close-ontology-loop" in stages:
        if "certify-standing" not in stages["close-ontology-loop"].get("requires", []):
            errors.append("ontology feedback must depend on formal certification")

    return errors


def evaluate_receipt(manifest: dict[str, Any], receipt: dict[str, Any]) -> str:
    terminal_refusals = set(manifest["refusals"]["terminal"])
    for violation in receipt.get("violations", []):
        if violation in terminal_refusals:
            return f"REFUSED:{violation}"

    for field in manifest["receipt"]["required_fields"]:
        if field not in receipt or receipt[field] in (None, "", [], {}):
            return "PARTIAL_ALIVE"

    stage_standing = receipt.get("stage_standing", {})
    for stage in manifest["stage"]:
        if stage_standing.get(stage["id"]) != "ALIVE":
            return "PARTIAL_ALIVE"

    if receipt.get("standing") != "ALIVE":
        return "PARTIAL_ALIVE"

    return "ALIVE"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root used to resolve --manifest when it is not given explicitly.",
    )
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)

    manifest_path = args.manifest
    if manifest_path is None:
        manifest_path = args.root.resolve() / "catalog" / "formal-discovery-loop.toml"
    args.manifest = manifest_path

    manifest = load_toml(args.manifest)
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
