#!/usr/bin/env python3
"""Fail-closed admission court for the canonical semantic-traversal contract."""

from __future__ import annotations

import argparse
import hashlib
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

RECEIPT_SCHEMA = "chatman.semantic-traversal-receipt.v1"
VERIFICATION_SCHEMA = "chatman.semantic-traversal-verification.v1"
RECEIPT_SCOPE = "canonical-contract-qualification"
EXCLUSIONS = (
    "no cross-repository runtime traversal claimed",
    "no consequential DO performed",
    "repository Crown unclaimed",
)


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
    for metric_id in sorted(REQUIRED_METRICS - metrics.keys()):
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


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def manufacture_receipt(path: Path, subject_sha: str) -> dict:
    findings = verify_path(path)
    if findings:
        raise ValueError("REFUSED:UNADMITTED_RECEIPT_SUBJECT")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "scope": RECEIPT_SCOPE,
        "subject": {
            "repository": "seanchatmangpt/chatman-ecosystem",
            "commit": subject_sha,
            "path": str(path),
            "sha256": _sha256_bytes(path.read_bytes()),
        },
        "correspondence": {"stages": list(EXPECTED_STAGES), "mode": "contract_admission"},
        "verification": {
            "schema": VERIFICATION_SCHEMA,
            "standing": "PARTIAL_ALIVE",
            "findings": [],
            "actuation_performed": False,
        },
        "exclusions": list(EXCLUSIONS),
    }
    receipt["integrity"] = {"algorithm": "sha256", "digest": _sha256_bytes(_canonical_json(receipt))}
    return receipt


def verify_receipt(receipt: dict, path: Path, subject_sha: str) -> list[str]:
    findings: list[str] = []
    if receipt.get("schema") != RECEIPT_SCHEMA:
        findings.append("REFUSED:RECEIPT_SCHEMA")
    if receipt.get("scope") != RECEIPT_SCOPE:
        findings.append("REFUSED:RECEIPT_SCOPE_DRIFT")

    subject = receipt.get("subject", {})
    if subject.get("repository") != "seanchatmangpt/chatman-ecosystem":
        findings.append("REFUSED:RECEIPT_REPOSITORY_DRIFT")
    if subject.get("commit") != subject_sha:
        findings.append("REFUSED:RECEIPT_EXACT_SUBJECT_DRIFT")
    if subject.get("path") != str(path):
        findings.append("REFUSED:RECEIPT_PATH_DRIFT")
    if subject.get("sha256") != _sha256_bytes(path.read_bytes()):
        findings.append("REFUSED:RECEIPT_CONTENT_DRIFT")

    correspondence = receipt.get("correspondence", {})
    if tuple(correspondence.get("stages", [])) != EXPECTED_STAGES:
        findings.append("REFUSED:RECEIPT_CORRESPONDENCE_DRIFT")
    if correspondence.get("mode") != "contract_admission":
        findings.append("REFUSED:RECEIPT_MODE_DRIFT")

    verification = receipt.get("verification", {})
    if verification.get("schema") != VERIFICATION_SCHEMA:
        findings.append("REFUSED:RECEIPT_VERIFICATION_SCHEMA")
    if verification.get("standing") != "PARTIAL_ALIVE":
        findings.append("REFUSED:RECEIPT_STANDING_DRIFT")
    if verification.get("findings") != []:
        findings.append("REFUSED:RECEIPT_FINDINGS_DRIFT")
    if verification.get("actuation_performed") is not False:
        findings.append("REFUSED:RECEIPT_ACTUATION_DRIFT")
    if receipt.get("exclusions") != list(EXCLUSIONS):
        findings.append("REFUSED:RECEIPT_EXCLUSIONS_DRIFT")

    integrity = receipt.get("integrity", {})
    unsigned = dict(receipt)
    unsigned.pop("integrity", None)
    expected_digest = _sha256_bytes(_canonical_json(unsigned))
    if integrity.get("algorithm") != "sha256" or integrity.get("digest") != expected_digest:
        findings.append("REFUSED:RECEIPT_INTEGRITY")

    if verify_path(path):
        findings.append("REFUSED:RECEIPT_SUBJECT_NOT_ADMITTED")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("catalog/semantic-traversal.toml"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--subject-sha")
    parser.add_argument("--receipt-out", type=Path)
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)

    try:
        findings = verify_path(args.path)
        if args.receipt_out:
            if not args.subject_sha:
                findings.append("REFUSED:MISSING_EXACT_SUBJECT")
            elif not findings:
                receipt = manufacture_receipt(args.path, args.subject_sha)
                args.receipt_out.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
        if args.replay:
            if not args.subject_sha:
                findings.append("REFUSED:MISSING_EXACT_SUBJECT")
            else:
                receipt = json.loads(args.replay.read_text())
                findings.extend(verify_receipt(receipt, args.path, args.subject_sha))
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        findings = [f"REFUSED:UNREADABLE_EVIDENCE:{exc}"]

    result = {
        "schema": VERIFICATION_SCHEMA,
        "subject": str(args.path),
        "subject_sha": args.subject_sha,
        "standing": "PARTIAL_ALIVE" if not findings else "BLOCKED",
        "actuation_performed": False,
        "receipt_written": str(args.receipt_out) if args.receipt_out and not findings else None,
        "receipt_replayed": str(args.replay) if args.replay and not findings else None,
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
