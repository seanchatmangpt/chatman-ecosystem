#!/usr/bin/env python3
"""Fail-closed admission court for the canonical semantic-traversal contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tomllib

EXPECTED_STAGES = (
    "graph",
    "query",
    "ggen",
    "admission",
    "runtime",
    "brce",
    "receipt",
    "replay",
)

REQUIRED_METRICS = {
    "semantic_fact_count",
    "interpretation_count",
    "projection_reuse_count",
    "qualification_count",
    "exact_head_qualified_count",
    "receipt_count",
}

REQUIRED_DERIVED = {
    "mean_semantic_traversal": "interpretation_count / semantic_fact_count",
    "projection_reuse_ratio": "projection_reuse_count / (projection_reuse_count + interpretation_count)",
    "exact_head_qualification_ratio": "exact_head_qualified_count / qualification_count",
}

REQUIRED_INVARIANTS = {
    "REPOSITORY_NOT_UNIT_OF_THOUGHT",
    "GENERATED_IS_PROJECTION",
    "EXACT_SUBJECT_QUALIFICATION",
    "NO_AMBIENT_DO",
}

REQUIRED_ROUTES = {
    "canonical-knowledge": ("repository:chatman-ecosystem", "SELECT"),
    "manufacture": ("repository:ggen", "CONSTRUCT"),
    "distribution": ("repository:ggen-marketplace", "CONSTRUCT"),
    "qualification": ("repository:ggen-ecosystem", "CONSTRUCT"),
    "actuation": ("repository:autofde", "DO"),
}


def _index_unique(items: list[dict], label: str, findings: list[str]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            findings.append(f"REFUSED:{label.upper()}_WITHOUT_ID")
            continue
        if item_id in indexed:
            findings.append(f"REFUSED:DUPLICATE_{label.upper()}:{item_id}")
            continue
        indexed[item_id] = item
    return indexed


def verify_document(document: dict) -> list[str]:
    findings: list[str] = []

    if document.get("schema") != "chatman.semantic-traversal.v1":
        findings.append("REFUSED:SEMANTIC_TRAVERSAL_SCHEMA")
    if document.get("unit_of_thought") != "capability":
        findings.append("REFUSED:REPOSITORY_AS_UNIT_OF_THOUGHT")

    stages = tuple(document.get("correspondence", {}).get("stages", []))
    if stages != EXPECTED_STAGES:
        findings.append("REFUSED:CORRESPONDENCE_DRIFT")

    metrics = _index_unique(document.get("metric", []), "metric", findings)
    missing_metrics = REQUIRED_METRICS - metrics.keys()
    for metric_id in sorted(missing_metrics):
        findings.append(f"REFUSED:MISSING_METRIC:{metric_id}")

    derived = _index_unique(document.get("derived_metric", []), "derived_metric", findings)
    for metric_id, expected_formula in REQUIRED_DERIVED.items():
        metric = derived.get(metric_id)
        if metric is None:
            findings.append(f"REFUSED:MISSING_DERIVED_METRIC:{metric_id}")
            continue
        if metric.get("formula") != expected_formula:
            findings.append(f"REFUSED:DERIVED_FORMULA_DRIFT:{metric_id}")
        if metric.get("zero_denominator") != "UNKNOWN":
            findings.append(f"REFUSED:ZERO_DENOMINATOR_NOT_UNKNOWN:{metric_id}")

    invariants = _index_unique(document.get("invariant", []), "invariant", findings)
    for invariant_id in sorted(REQUIRED_INVARIANTS - invariants.keys()):
        findings.append(f"REFUSED:MISSING_INVARIANT:{invariant_id}")

    routes = _index_unique(document.get("route", []), "route", findings)
    for route_id, (expected_owner, expected_class) in REQUIRED_ROUTES.items():
        route = routes.get(route_id)
        if route is None:
            findings.append(f"REFUSED:MISSING_ROUTE:{route_id}")
            continue
        if route.get("owner") != expected_owner:
            findings.append(f"REFUSED:ROUTE_OWNER_DRIFT:{route_id}")
        if route.get("class") != expected_class:
            findings.append(f"REFUSED:ROUTE_CLASS_DRIFT:{route_id}")
        if expected_class == "DO" and route.get("broker_required") is not True:
            findings.append(f"REFUSED:AMBIENT_DO:{route_id}")

    for route_id, route in routes.items():
        action_class = route.get("class")
        if action_class not in {"SELECT", "CONSTRUCT", "DO"}:
            findings.append(f"REFUSED:UNKNOWN_ACTION_CLASS:{route_id}")
        if action_class == "DO" and route.get("broker_required") is not True:
            finding = f"REFUSED:AMBIENT_DO:{route_id}"
            if finding not in findings:
                findings.append(finding)

    return findings


def verify_path(path: Path) -> list[str]:
    with path.open("rb") as handle:
        return verify_document(tomllib.load(handle))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("catalog/semantic-traversal.toml"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        findings = verify_path(args.path)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        findings = [f"REFUSED:UNREADABLE_CONTRACT:{exc}"]

    result = {
        "schema": "chatman.semantic-traversal-verification.v1",
        "subject": str(args.path),
        "standing": "PARTIAL_ALIVE" if not findings else "BLOCKED",
        "actuation_performed": False,
        "findings": findings,
    }

    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    elif findings:
        for finding in findings:
            print(finding, file=sys.stderr)
    else:
        print("VERIFIED semantic traversal contract")

    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
