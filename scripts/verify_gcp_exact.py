#!/usr/bin/env python3
"""Verify the canonical GCP exact-conformance control-plane contract.

This verifier proves structural admission only. It never manufactures live GCP
standing from static catalog data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tomllib

REQUIRED_SOURCES = {
    "discovery",
    "googleapis-proto",
    "service-config",
    "asset-inventory",
    "audit-logs",
    "iam",
    "quota",
    "long-running-operations",
    "human-docs",
    "empirical-observation",
}
ALLOWED_STANDINGS = {
    "UNKNOWN",
    "PARTIAL_ALIVE",
    "ALIVE",
    "BLOCKED",
    "BUILD_BROKEN",
    "UNSUPPORTED",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
GAP_FIELDS = (
    "unknown_units",
    "partial_alive_units",
    "blocked_units",
    "unsupported_units",
    "refused_units",
    "duplicate_units",
    "unreceipted_alive_units",
)


def verify(path: Path) -> dict[str, object]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    failures: list[str] = []

    if data.get("schema") != "chatman.gcp-exact-conformance.v1":
        failures.append("REFUSED:SCHEMA_IDENTITY_MISMATCH")

    standing = data.get("standing")
    if standing not in ALLOWED_STANDINGS:
        failures.append("REFUSED:INVALID_STANDING")

    subjects = data.get("subjects", [])
    ids = [str(subject.get("id", "")) for subject in subjects]
    if len(ids) != len(set(ids)):
        failures.append("REFUSED:DUPLICATE_SUBJECT_ID")
    known_ids = set(ids)
    for subject in subjects:
        subject_id = str(subject.get("id", ""))
        if not SHA40.fullmatch(str(subject.get("sha", ""))):
            failures.append(f"REFUSED:NON_EXACT_SHA:{subject_id}")
        if subject.get("standing") not in ALLOWED_STANDINGS:
            failures.append(f"REFUSED:INVALID_SUBJECT_STANDING:{subject_id}")
        for dependency in subject.get("depends_on", []):
            if dependency not in known_ids:
                failures.append(f"REFUSED:IMPLICIT_DEPENDENCY:{subject_id}:{dependency}")

    sources = data.get("contract_sources", [])
    source_ids = [str(source.get("id", "")) for source in sources if source.get("required")]
    observed_sources = set(source_ids)
    missing = sorted(REQUIRED_SOURCES - observed_sources)
    extra = sorted(observed_sources - REQUIRED_SOURCES)
    duplicates = sorted({source for source in source_ids if source_ids.count(source) > 1})
    if missing:
        failures.append("REFUSED:MISSING_CONTRACT_SOURCES:" + ",".join(missing))
    if extra:
        failures.append("REFUSED:UNADMITTED_CONTRACT_SOURCES:" + ",".join(extra))
    if duplicates:
        failures.append("REFUSED:DUPLICATE_CONTRACT_SOURCES:" + ",".join(duplicates))

    exactness = data.get("exactness", {})
    admitted = int(exactness.get("admitted_contract_units", 0))
    paired = int(exactness.get("paired_alive_units", 0))
    claim = bool(exactness.get("claim", False))
    gaps = {field: int(exactness.get(field, 0)) for field in GAP_FIELDS}

    if paired > admitted:
        failures.append("REFUSED:PAIRED_COUNT_EXCEEDS_ADMITTED")

    required_subjects_alive = all(
        not subject.get("required") or subject.get("standing") == "ALIVE"
        for subject in subjects
    )
    exact_ready = (
        admitted > 0
        and paired == admitted
        and all(value == 0 for value in gaps.values())
        and required_subjects_alive
    )

    if claim and not exact_ready:
        failures.append("REFUSED:EXACTNESS_WITHOUT_COMPLETE_PAIRED_EVIDENCE")
    if standing == "ALIVE" and not claim:
        failures.append("REFUSED:ALIVE_WITHOUT_EXACTNESS_CLAIM")
    if standing == "ALIVE" and not exact_ready:
        failures.append("REFUSED:ALIVE_WITHOUT_EXACTNESS_CLOSURE")

    invariants = data.get("invariants", {})
    required_invariants = {
        "all_required_sources_present",
        "all_subjects_exact_sha",
        "select_construct_do_separated",
        "zero_unreceipted_actuation",
        "unknown_ne_alive",
        "exactness_requires_paired_receipts",
        "exactness_requires_zero_gaps",
    }
    false_invariants = sorted(
        name for name in required_invariants if invariants.get(name) is not True
    )
    if false_invariants:
        failures.append("REFUSED:INVARIANT_NOT_ADMITTED:" + ",".join(false_invariants))

    return {
        "status": "ALIVE" if not failures else "REFUSED",
        "subject": str(path),
        "standing": standing,
        "exactness_claim": claim,
        "exact_ready": exact_ready,
        "admitted_contract_units": admitted,
        "paired_alive_units": paired,
        "required_source_count": len(REQUIRED_SOURCES),
        "required_subjects_alive": required_subjects_alive,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("catalog/gcp-exact.toml"),
    )
    args = parser.parse_args()
    result = verify(args.path)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ALIVE" else 1


if __name__ == "__main__":
    sys.exit(main())
