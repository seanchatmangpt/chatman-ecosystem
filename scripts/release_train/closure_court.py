#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SPEC = {"FINAL_SPEC", "IMPLEMENTED_CANDIDATE", "CLOSED_DESIGN", "EXECUTABLE_CONTRACT", "NOT_A_SPEC", "SUPERSEDED"}
IMPL = {"ALIVE", "PARTIAL_ALIVE", "PLANNED", "NOT_CLAIMED", "BLOCKED", "REFUSED", "UNSUPPORTED", "SUPERSEDED"}
DIST = {"PUBLISHED", "TAGGED", "BLOCKED", "NOT_APPLICABLE"}
AUTH = {"NONE": 0, "SELECT": 1, "CONSTRUCT": 2, "DO": 3}


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    refusals: list[str] = []
    remaining: list[str] = []
    rows = data.get("subjects")
    if not isinstance(rows, list) or not rows:
        refusals.append("REFUSED:MALFORMED:subjects")
        rows = []

    seen: set[str] = set()
    transient = {x.get("sha") for x in data.get("transient_heads", []) if isinstance(x, dict)}

    for row in rows:
        sid = row.get("subject_id")
        if not isinstance(sid, str) or not sid:
            refusals.append("REFUSED:MALFORMED:subject_id")
            continue
        if sid in seen:
            refusals.append(f"REFUSED:DUPLICATE_SUBJECT:{sid}")
        seen.add(sid)

        sha = row.get("sha", "")
        if not isinstance(sha, str) or not SHA40.fullmatch(sha):
            refusals.append(f"REFUSED:EXACT_SHA:{sid}")

        spec = row.get("spec_standing")
        impl = row.get("impl_standing")
        if spec not in SPEC:
            refusals.append(f"REFUSED:SPEC_STANDING:{sid}:{spec}")
        if impl not in IMPL:
            refusals.append(f"REFUSED:IMPL_STANDING:{sid}:{impl}")
        if impl in {"BLOCKED", "REFUSED", "UNSUPPORTED"} and not row.get("impl_type"):
            refusals.append(f"REFUSED:TYPED_TERMINAL:{sid}:impl")
        if spec == "SUPERSEDED" or impl == "SUPERSEDED":
            successor = row.get("successor")
            if not isinstance(successor, dict) or not SHA40.fullmatch(str(successor.get("sha", ""))):
                refusals.append(f"REFUSED:SUCCESSOR:{sid}")

        ceiling = row.get("authority_ceiling", "NONE")
        claimed = row.get("authority_claimed", "NONE")
        if ceiling not in AUTH or claimed not in AUTH or AUTH.get(claimed, 99) > AUTH.get(ceiling, -1):
            refusals.append(f"REFUSED:AUTHORITY:{sid}:{claimed}>{ceiling}")

        courts = row.get("courts", [])
        if impl in {"ALIVE", "PARTIAL_ALIVE"}:
            if not any(c.get("result") == "PASS" and c.get("sha") == sha for c in courts if isinstance(c, dict)):
                refusals.append(f"REFUSED:ALIVE_WITHOUT_EXACT_PASS:{sid}")
        for c in courts:
            if not isinstance(c, dict):
                refusals.append(f"REFUSED:MALFORMED_COURT:{sid}")
                continue
            if c.get("sha") != sha:
                refusals.append(f"REFUSED:COURT_SUBJECT_SPLIT:{sid}:{c.get('name', '?')}")
            if c.get("required", True) and c.get("result") == "FAIL":
                refusals.append(f"REFUSED:REQUIRED_COURT_FAILED:{sid}:{c.get('name', '?')}")

        for pin in row.get("pins", []):
            if isinstance(pin, dict) and pin.get("sha") in transient:
                refusals.append(f"REFUSED:TRANSIENT_PIN:{sid}:{pin.get('sha')}")

        dist = row.get("distribution", {"state": "NOT_APPLICABLE"})
        state = dist.get("state")
        if state not in DIST:
            refusals.append(f"REFUSED:DISTRIBUTION_STATE:{sid}:{state}")
        if state == "BLOCKED":
            dtype = dist.get("type")
            if not dtype:
                refusals.append(f"REFUSED:TYPED_TERMINAL:{sid}:distribution")
            else:
                remaining.append(f"{sid}:distribution:BLOCKED({dtype})")
        elif state in {"PUBLISHED", "TAGGED"}:
            dsha = dist.get("sha")
            if dsha != sha:
                refusals.append(f"REFUSED:DISTRIBUTION_SUBJECT_SPLIT:{sid}:{dsha}")

    standing = "REFUSED" if refusals else ("PARTIAL_ALIVE" if remaining else "ALIVE")
    receipt = {
        "schema": "https://chatman.dev/release/v26.9.24/closure-receipt/v1",
        "release": data.get("release"),
        "normative_ledger": data.get("normative_ledger"),
        "standing": standing,
        "subject_count": len(rows),
        "refusals": sorted(set(refusals)),
        "remaining": sorted(set(remaining)),
        "subjects": sorted(f"{r.get('subject_id')}={r.get('repository')}@{r.get('sha')}" for r in rows),
        "authority": "NONE",
    }
    receipt["receipt_digest"] = canonical_digest(receipt)
    return receipt


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: closure_court.py release/v26.9.24/closure.json", file=sys.stderr)
        return 64
    data = json.loads(Path(argv[1]).read_text())
    receipt = evaluate(data)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["standing"] in {"ALIVE", "PARTIAL_ALIVE"} else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
