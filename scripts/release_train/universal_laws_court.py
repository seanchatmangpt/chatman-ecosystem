#!/usr/bin/env python3
"""Dependency-free executable court for the Universal Laws portable vectors.

The court classifies conformance evidence only. It has authority=NONE and
cannot issue DO authority or operational standing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

KNOWN_LAWS = {
    "L1", "L2", "L3", "L4", "L5", "L6", "L7",
    "L8", "L9", "L10", "L11", "L12", "NULL",
}
TERMINAL_RESULTS = {"ADMISSIBLE", "REFUSED", "NONCONFORMANT", "UNKNOWN"}


@dataclass(frozen=True)
class Evaluation:
    case_id: str
    law: str
    result: str
    attempt_observed: bool
    violation_observed: bool
    reason: str


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def evaluate_case(case: dict[str, Any]) -> Evaluation:
    case_id = str(case.get("id", ""))
    law = str(case.get("law", ""))

    if not case_id or law not in KNOWN_LAWS:
        return Evaluation(
            case_id or "UNKNOWN",
            law or "UNKNOWN",
            "UNKNOWN",
            True,
            False,
            "unknown_case_or_law",
        )

    result, reason = _evaluate_known(case)
    return Evaluation(
        case_id=case_id,
        law=law,
        result=result,
        attempt_observed=True,
        violation_observed=result in {"REFUSED", "NONCONFORMANT"},
        reason=reason,
    )


def _evaluate_known(case: dict[str, Any]) -> tuple[str, str]:
    law = case["law"]

    if law == "L1":
        if case.get("hidden"):
            return "REFUSED", "hidden_load_bearing_semantics"
        return "ADMISSIBLE", "explicit_or_unknown"

    if law == "L2":
        if len(case.get("owners", [])) != 1:
            return "REFUSED", "canonical_owner_cardinality"
        return "ADMISSIBLE", "single_owner"

    if law == "L3":
        if case.get("select") and case.get("do_without_authority"):
            return "REFUSED", "select_performed_do"
        return "ADMISSIBLE", "phase_separation"

    if law == "L4":
        if case.get("receipt") and case.get("authority") is False:
            return "REFUSED", "non_authority_artifact_used_as_authority"
        return "ADMISSIBLE", "authority_independent"

    if law == "L5":
        different_subject = case.get("evidence_subject") != case.get("claim_subject")
        if different_subject and not case.get("qualified_equivalence"):
            return "REFUSED", "cross_subject_standing_transfer"
        if (
            different_subject
            and case.get("qualified_equivalence")
            and not case.get("bounds")
        ):
            return "REFUSED", "unbounded_equivalence"
        return "ADMISSIBLE", "exact_or_bounded_equivalent_subject"

    if law == "L6":
        if case.get("projection") and not case.get("derived_from"):
            return "REFUSED", "derived_state_without_lineage"
        return "ADMISSIBLE", "lineage_bound"

    if law == "L7":
        if case.get("outcome") == "UNKNOWN" and case.get("standing") == "ALIVE":
            return "REFUSED", "unknown_promoted_to_success"
        return "ADMISSIBLE", "bounded_consequence"

    if law == "L8":
        if case.get("reachable_lawful_edges", 0) > 0 and case.get("decision") == "STOP":
            return "REFUSED", "edge_failure_promoted_to_global_stop"
        return "ADMISSIBLE", "edge_local_failure"

    if law == "L9":
        invalid = (
            case.get("replacement")
            and not case.get("preserved_constraints")
            and not case.get("same_subject_falsifier")
        )
        if invalid:
            return "REFUSED", "reverse_chesterton_violation"
        return "ADMISSIBLE", "replacement_qualified"

    if law == "L10":
        invalid = (
            case.get("guard_removed")
            and not case.get("origin_recovered")
            and not case.get("falsifier")
        )
        if invalid:
            return "REFUSED", "negative_chesterton_violation"
        return "ADMISSIBLE", "constraint_recovered_or_falsified"

    if law == "L11":
        if case.get("reproduced_failure") and not case.get("durable_constraint"):
            return "NONCONFORMANT", "failure_not_distilled"
        return "ADMISSIBLE", "failure_distilled"

    if law == "L12":
        if case.get("authority_issued_by_test"):
            return "REFUSED", "qualification_issued_authority"
        return "ADMISSIBLE", "qualification_non_authoritative"

    if law == "NULL":
        if (
            case.get("adopted")
            and case.get("candidate_value", 0) < case.get("null_value", 0)
        ):
            return "REFUSED", "candidate_below_null"
        return "ADMISSIBLE", "not_below_null"

    return "UNKNOWN", "unreachable"


def run(path: str) -> tuple[dict[str, Any], int]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = document.get("cases", [])
    evaluations = [evaluate_case(case) for case in cases]
    expected_by_id = {case.get("id"): case.get("expected") for case in cases}

    mismatches = []
    for evaluation in evaluations:
        expected = expected_by_id.get(evaluation.case_id)
        if expected not in TERMINAL_RESULTS or expected != evaluation.result:
            mismatches.append(
                {
                    "id": evaluation.case_id,
                    "expected": expected,
                    "observed": evaluation.result,
                }
            )

    receipt: dict[str, Any] = {
        "schema": "https://chatman.dev/universal-laws/court-receipt/v1",
        "subject": str(Path(path)),
        "cases": len(evaluations),
        "attempts_observed": sum(e.attempt_observed for e in evaluations),
        "violations_observed": sum(e.violation_observed for e in evaluations),
        "mismatches": mismatches,
        "authority": "NONE",
        "standing": "ALIVE" if evaluations and not mismatches else "REFUSED",
        "results": [asdict(evaluation) for evaluation in evaluations],
    }
    receipt["digest"] = canonical_digest(receipt)
    return receipt, 0 if receipt["standing"] == "ALIVE" else 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Universal Laws portable conformance vectors"
    )
    parser.add_argument("vectors", help="path to tests/universal-laws/vectors.json")
    args = parser.parse_args()
    receipt, code = run(args.vectors)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
