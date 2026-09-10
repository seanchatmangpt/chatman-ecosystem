#!/usr/bin/env python3
"""Validate the canonical BFCC gate catalog and evaluate assessment receipts.

The verifier checks manifest well-formedness and receipt evidence coverage. It does
not itself perform any DO action -- OBSERVE/VERIFY only -- and it must never let
partial gate coverage round up to BFCC-ALIVE.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "catalog" / "bfcc.toml"

EXPECTED_GATE_LETTERS = {"C", "A", "D", "S", "G", "Sigma", "E", "T", "W", "I"}

SYNERGY_KEYWORDS = ("synerg", "composed-behavior", "composition benefit", "whole-system")


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate_manifest(catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    gates = catalog.get("gate", [])
    letters_present: dict[str, dict[str, Any]] = {}
    for index, gate in enumerate(gates):
        letter = gate.get("letter")
        if not isinstance(letter, str) or not letter:
            errors.append(f"gate[{index}] requires a non-empty letter")
            continue
        if letter in letters_present:
            errors.append(f"duplicate gate letter: {letter}")
            continue
        letters_present[letter] = gate

        falsifier = gate.get("falsifier")
        if not isinstance(falsifier, str) or not falsifier.strip():
            errors.append(f"gate {letter} requires a non-empty falsifier")

        fuller_principle = gate.get("fuller_principle", "")
        engineering_projection = gate.get("engineering_projection", "")
        if not isinstance(fuller_principle, str) or not fuller_principle.strip():
            errors.append(f"gate {letter} requires a non-empty fuller_principle")
        if not isinstance(engineering_projection, str) or not engineering_projection.strip():
            errors.append(f"gate {letter} requires a non-empty engineering_projection")
        if (
            isinstance(fuller_principle, str)
            and isinstance(engineering_projection, str)
            and fuller_principle.strip()
            and engineering_projection.strip()
            and engineering_projection.strip() == fuller_principle.strip()
        ):
            errors.append(f"FULLER_LAUNDERING: gate {letter} projection restates its principle verbatim")

    missing_letters = sorted(EXPECTED_GATE_LETTERS - set(letters_present))
    if missing_letters:
        errors.append(f"missing gates: {', '.join(missing_letters)}")

    authority = catalog.get("authority", {})
    if authority.get("bfcc_grants_do_authority") is not False:
        errors.append("authority.bfcc_grants_do_authority must deny DO (false)")
    if authority.get("plan_grants_authority") is not False:
        errors.append("authority.plan_grants_authority must deny DO (false)")
    if authority.get("proof_grants_authority") is not False:
        errors.append("authority.proof_grants_authority must deny DO (false)")

    required_fields = catalog.get("receipt", {}).get("required_fields", [])
    if not isinstance(required_fields, list) or not required_fields:
        errors.append("receipt.required_fields must be non-empty")

    return errors


def evaluate_receipt(catalog: dict[str, Any], receipt: dict[str, Any]) -> str:
    mandatory_gates = [gate for gate in catalog.get("gate", []) if gate.get("mandatory") is True]

    evidence_per_gate = receipt.get("evidence_per_gate", {}) or {}
    falsifier_per_gate = receipt.get("falsifier_per_gate", {}) or {}

    missing_gate_letters = []
    for gate in mandatory_gates:
        letter = gate.get("letter")
        has_evidence = bool(evidence_per_gate.get(letter))
        has_falsifier = bool(falsifier_per_gate.get(letter))
        if not has_evidence or not has_falsifier:
            missing_gate_letters.append(letter)

    if missing_gate_letters and receipt.get("standing") == "BFCC-ALIVE":
        return "REFUSED:AVERAGED_FAILED_GATE"

    prose_fields = " ".join(
        str(receipt.get(field, ""))
        for field in ("contradictions", "unresolved_gaps", "standing")
    )
    prose_fields += " " + json.dumps(evidence_per_gate)
    synergy_claimed = any(keyword in prose_fields.lower() for keyword in SYNERGY_KEYWORDS)
    sigma_evidence = receipt.get("sigma_evidence")
    if synergy_claimed and not sigma_evidence:
        return "REFUSED:UNFALSIFIED_SYNERGY_CLAIM"

    inventory_examined = receipt.get("inventory_examined")
    if not inventory_examined:
        return "REFUSED:MISSING_INVENTORY"

    cited_subjects: set[str] = set()
    cited_revisions: set[str] = set()
    for entry in evidence_per_gate.values():
        if isinstance(entry, dict):
            if entry.get("subject"):
                cited_subjects.add(entry["subject"])
            if entry.get("revision"):
                cited_revisions.add(entry["revision"])

    receipt_subject = receipt.get("subject")
    receipt_revision = receipt.get("revision")
    if cited_subjects and receipt_subject not in cited_subjects:
        return "REFUSED:STANDING_TRANSFERRED"
    if cited_revisions and receipt_revision not in cited_revisions:
        return "REFUSED:STANDING_TRANSFERRED"

    if missing_gate_letters:
        return "BFCC-PARTIAL"

    return "BFCC-ALIVE"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    manifest_path = args.manifest
    if manifest_path is None:
        manifest_path = args.root.resolve() / "catalog" / "bfcc.toml"
    args.manifest = manifest_path

    catalog = load_toml(args.manifest)
    errors = validate_manifest(catalog)
    if errors:
        if args.json:
            print(json.dumps({"standing": "REFUSED:MANIFEST_INVALID", "errors": errors}))
        else:
            for error in errors:
                print(f"REFUSED:MANIFEST_INVALID:{error}")
        return 2

    if args.receipt is None:
        if args.json:
            print(json.dumps({"standing": "MANIFEST_ALIVE"}))
        else:
            print("MANIFEST_ALIVE")
        return 0

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    standing = evaluate_receipt(catalog, receipt)
    if args.json:
        print(json.dumps({"standing": standing}))
    else:
        print(standing)

    if standing == "BFCC-ALIVE":
        return 0
    if standing.startswith("REFUSED:"):
        return 2
    return 3


if __name__ == "__main__":
    sys.exit(main())
