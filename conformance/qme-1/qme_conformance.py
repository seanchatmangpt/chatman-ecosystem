#!/usr/bin/env python3
"""QME-1 semantic conformance court.

Stdlib only. The court evaluates evidence records; it grants no authority and
performs no actuation.
"""

import json
import sys

PROHIBITED_AUTHORITY_BASES = {
    "capability",
    "evidence",
    "signature",
    "plan",
    "receipt",
    "semantic_truth",
    "ontology_inference",
    "model_output",
    "external_allow",
}


def court(record):
    errors = []
    subject = record.get("subject")

    if record.get("receipt", {}).get("subject") != subject:
        errors.append("EXACT_SUBJECT")

    if (
        record.get("consequence", {}).get("bounded") is not True
        or record.get("value", {}).get("bounded") is not True
    ):
        errors.append("MXINF")

    if record.get("replay", {}).get("actuates") is not False:
        errors.append("REPLAY_ACTUATES")

    if (
        record.get("authority_ceiling") == "do"
        and record.get("observation", {}).get("independent") is not True
    ):
        errors.append("SELF_OBSERVED_DO")

    attempt = record.get("attempt", {})
    if attempt.get("observed") is not True:
        errors.append("VACUOUS_COURT")
    if attempt.get("violation_observed") is True:
        errors.append("VIOLATION_OBSERVED")

    for claim in record.get("semantic_claims", []):
        if claim.get("consequential") is True and (
            claim.get("visible") is not True or not claim.get("owner")
        ):
            errors.append("HIDDEN_SEMANTICS")

    if record.get("authority_ceiling") == "do":
        if any(
            source in PROHIBITED_AUTHORITY_BASES
            for source in record.get("authority_basis", [])
        ):
            errors.append("AUTHORITY_PROMOTION")

    generated = record.get("generated", {})
    if generated.get("is_projection") and not all(
        generated.get(key) for key in ("source", "generator", "digest")
    ):
        errors.append("HIDDEN_GENERATION")

    for item in record.get("negative_knowledge", []):
        if item.get("subject") != subject:
            errors.append("NEGATIVE_SUBJECT")

    for retirement in record.get("guard_retirements", []):
        if (
            retirement.get("subject") != subject
            or not retirement.get("same_subject_evidence")
            or not retirement.get("falsifier")
        ):
            errors.append("GUARD_RETIREMENT_UNGROUNDED")

    for candidate in record.get("external_candidates", []):
        if candidate.get("promotes_to_local_do") is True:
            errors.append("EXTERNAL_AUTHORITY_PROMOTION")

    net = record.get("value", {}).get("net")
    if (
        isinstance(net, (int, float))
        and net < 0
        and record.get("standing") == "ALIVE"
    ):
        errors.append("NEGATIVE_VALUE_PROMOTED")

    if any(
        not concept or not owner
        for concept, owner in record.get("canonical_owners", {}).items()
    ):
        errors.append("CANONICAL_OWNER_MISSING")

    if not record.get("falsifiers"):
        errors.append("FALSIFIERS_MISSING")

    return sorted(set(errors))


def main():
    result = 0
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)

        got = court(record)
        expected = sorted(record.get("_expected_errors", []))
        if got != expected:
            print(path, "FAIL", got, "expected", expected)
            result = 1
        else:
            print(path, "PASS", got)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
