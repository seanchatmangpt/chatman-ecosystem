#!/usr/bin/env python3
"""Architecture Championship Court for versioned DfCM Industry Closure claims.

This court can falsify a specific architecture version. It cannot grant DO authority
and it never erases an earlier defeat by evaluating a later version.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def compare(court: dict, challenger: dict | None) -> dict:
    claim = court["claim"]
    if not claim.get("version") or not claim.get("exact_subject"):
        raise ValueError("UNVERSIONED_ARCHITECTURE_CLAIM")
    if court.get("authority") != "NONE":
        raise ValueError("COURT_CANNOT_GRANT_DO")
    falsifier = court.get("falsifier", {})
    if falsifier.get("type") != "STRICT_PARETO_DOMINANCE":
        raise ValueError("MISSING_STRICT_DOMINANCE_FALSIFIER")

    result = {
        "schema": "chatman-fuller.architecture-court-receipt.v1",
        "subject": claim["exact_subject"],
        "version": claim["version"],
        "boundary_digest": claim["boundary_digest"],
        "authority": "NONE",
        "standing": "CANDIDATE",
        "falsified": False,
        "challenger": None,
        "dimension_results": {},
    }

    if challenger is None:
        result["disposition"] = "UNFALSIFIED_NO_CHALLENGER"
        result["receipt_digest"] = digest(result)
        return result

    if challenger.get("boundary_digest") != claim.get("boundary_digest"):
        result["disposition"] = "REFUSED_BOUNDARY_MISMATCH"
        result["challenger"] = challenger.get("name")
        result["receipt_digest"] = digest(result)
        return result
    if challenger.get("authority") != "NONE":
        result["disposition"] = "REFUSED_AUTHORITY_LAUNDERING"
        result["challenger"] = challenger.get("name")
        result["receipt_digest"] = digest(result)
        return result

    baseline = claim["metrics"]
    candidate = challenger["metrics"]
    dimensions = court["dimensions"]

    no_worse = True
    strictly_better = False
    for name, direction in dimensions.items():
        if name not in baseline or name not in candidate:
            raise ValueError(f"MISSING_DIMENSION:{name}")
        base = baseline[name]
        other = candidate[name]
        if direction == "MAX":
            relation = "BETTER" if other > base else "EQUAL" if other == base else "WORSE"
        elif direction == "MIN":
            relation = "BETTER" if other < base else "EQUAL" if other == base else "WORSE"
        else:
            raise ValueError(f"INVALID_DIRECTION:{name}:{direction}")
        result["dimension_results"][name] = relation
        no_worse = no_worse and relation != "WORSE"
        strictly_better = strictly_better or relation == "BETTER"

    result["challenger"] = challenger["name"]
    result["synthetic_challenger"] = bool(challenger.get("synthetic", False))

    if no_worse and strictly_better:
        result["standing"] = "FALSIFIED"
        result["falsified"] = True
        result["disposition"] = "STRICTLY_DOMINATED"
    else:
        result["disposition"] = "CHALLENGER_DID_NOT_DOMINATE"

    result["receipt_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("court")
    parser.add_argument("--challenger")
    parser.add_argument("--expect", choices=["CANDIDATE", "FALSIFIED"])
    args = parser.parse_args()

    court = json.loads(Path(args.court).read_text())
    challenger = json.loads(Path(args.challenger).read_text()) if args.challenger else None
    first = compare(court, challenger)
    second = compare(court, challenger)
    if first != second:
        print("REFUSED[NON_DETERMINISTIC_COURT]")
        return 3

    print(json.dumps(first, sort_keys=True, separators=(",", ":")))
    if args.expect and first["standing"] != args.expect:
        print(f"REFUSED[EXPECTED_{args.expect}_GOT_{first['standing']}]")
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
