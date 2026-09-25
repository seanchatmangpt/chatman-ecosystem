from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.release_train.cross_product_court.model import canonical_digest

SCHEMA = "https://chatman.dev/release-closure-court/receipt/v1"

_SHA40 = re.compile(r"^[0-9a-f]{40}$")

SPEC_STANDINGS = frozenset(
    {"FINAL_SPEC", "MERGED", "SUPERSEDED", "REFUSED", "UNSUPPORTED", "BLOCKED", "NOT_A_SPEC"}
)
IMPL_TERMINAL = frozenset(
    {
        "ALIVE",
        "PARTIAL_ALIVE",
        "PLANNED",
        "NOT_CLAIMED",
        "BLOCKED",
        "REFUSED",
        "UNSUPPORTED",
        "SUPERSEDED",
    }
)
COURT_RESULTS = frozenset({"PASS", "FAIL", "BASELINE_BLOCKER", "BLOCKED"})
AUTHORITY_RANK = {"NONE": 0, "SELECT": 1, "CONSTRUCT": 2, "DO": 3}

RULES = (
    "REFUSED:MALFORMED_ROW",
    "REFUSED:DUPLICATE_SUBJECT_ID",
    "REFUSED:MISSING_EXACT_SHA",
    "REFUSED:UNKNOWN_REQUIRED_SUBJECT",
    "REFUSED:SUPERSEDED_WITHOUT_SUCCESSOR",
    "REFUSED:SUCCESSOR_UNBOUND",
    "REFUSED:FINAL_SPEC_AS_IMPLEMENTATION_EVIDENCE",
    "REFUSED:REQUIRED_COURT_FAILED",
    "REFUSED:COURT_SUBJECT_SPLIT",
    "REFUSED:AUTHORITY_ESCALATION",
    "REFUSED:TRANSIENT_PIN",
    "REFUSED:DUPLICATE_CANONICAL_OWNER",
    "REFUSED:BLOCKED_WITHOUT_TYPE",
)


@dataclass(frozen=True, slots=True)
class Verdict:
    standing: str
    refusals: tuple[str, ...]
    remaining: tuple[str, ...]
    receipt: dict[str, Any]


def _row_refusals(row: dict[str, Any]) -> list[str]:
    sid = row.get("subject_id", "?")
    out: list[str] = []
    for key in ("subject_id", "repository", "artifact", "spec_standing", "impl_standing"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:{key}")
    if out:
        return out
    if not _SHA40.fullmatch(str(row.get("sha", ""))):
        out.append(f"REFUSED:MISSING_EXACT_SHA:{sid}")
    spec, impl = row["spec_standing"], row["impl_standing"]
    required = bool(row.get("required", True))
    if spec not in SPEC_STANDINGS:
        out.append(f"REFUSED:UNKNOWN_REQUIRED_SUBJECT:{sid}:spec={spec}")
    if impl not in IMPL_TERMINAL and required:
        out.append(f"REFUSED:UNKNOWN_REQUIRED_SUBJECT:{sid}:impl={impl}")
    for label, value in (("spec", spec), ("impl", impl)):
        if value in {"BLOCKED", "REFUSED", "UNSUPPORTED"} and not str(
            row.get(f"{label}_type", "")
        ).strip():
            out.append(f"REFUSED:BLOCKED_WITHOUT_TYPE:{sid}:{label}")
    if spec == "SUPERSEDED" or impl == "SUPERSEDED":
        succ = row.get("successor")
        if not isinstance(succ, dict):
            out.append(f"REFUSED:SUPERSEDED_WITHOUT_SUCCESSOR:{sid}")
        elif not _SHA40.fullmatch(str(succ.get("sha", ""))) or not succ.get("repository"):
            out.append(f"REFUSED:SUCCESSOR_UNBOUND:{sid}")
    courts = row.get("courts", [])
    passing_impl = [
        c
        for c in courts
        if c.get("result") == "PASS" and c.get("kind", "implementation") == "implementation"
    ]
    if impl in {"ALIVE", "PARTIAL_ALIVE"} and not passing_impl:
        out.append(f"REFUSED:FINAL_SPEC_AS_IMPLEMENTATION_EVIDENCE:{sid}")
    for court in courts:
        name = court.get("court", "?")
        if court.get("result") not in COURT_RESULTS:
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:court={name}")
        elif court.get("result") == "FAIL" and court.get("required", True):
            out.append(f"REFUSED:REQUIRED_COURT_FAILED:{sid}:{name}")
        if court.get("sha") != row.get("sha"):
            out.append(f"REFUSED:COURT_SUBJECT_SPLIT:{sid}:{name}")
    ceiling = row.get("authority_ceiling", "NONE")
    claimed = row.get("authority_claimed", "NONE")
    if AUTHORITY_RANK.get(claimed, 99) > AUTHORITY_RANK.get(ceiling, -1):
        out.append(f"REFUSED:AUTHORITY_ESCALATION:{sid}:{claimed}>{ceiling}")
    return out


def evaluate(closure: dict[str, Any]) -> Verdict:
    rows = closure.get("subjects", [])
    refusals: list[str] = []
    if not rows:
        refusals.append("REFUSED:MALFORMED_ROW:closure:subjects-empty")
    ids = [r.get("subject_id") for r in rows]
    for dup in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        refusals.append(f"REFUSED:DUPLICATE_SUBJECT_ID:{dup}")
    for row in rows:
        refusals.extend(_row_refusals(row))

    transient = {t["sha"]: t for t in closure.get("transient_heads", [])}
    for row in rows:
        for pin in row.get("pins", []):
            hit = transient.get(pin.get("sha"))
            if hit is not None:
                refusals.append(
                    f"REFUSED:TRANSIENT_PIN:{row.get('subject_id')}:{pin.get('sha')}"
                    f"->durable={hit.get('replaced_by')}"
                )

    owners: dict[str, set[tuple[str, str]]] = {}
    for row in rows:
        rfc = row.get("rfc_id")
        if rfc and row.get("spec_standing") == "FINAL_SPEC":
            owners.setdefault(rfc, set()).add((row.get("repository"), row.get("artifact")))
    for rfc, where in sorted(owners.items()):
        if len(where) > 1:
            refusals.append(f"REFUSED:DUPLICATE_CANONICAL_OWNER:{rfc}")

    remaining = tuple(
        sorted(
            f"{r.get('subject_id')}:{label}:{r.get(label + '_standing')}"
            f"({r.get(label + '_type', '')})"
            for r in rows
            for label in ("spec", "impl")
            if r.get(label + "_standing") in {"BLOCKED", "UNSUPPORTED", "REFUSED"}
        )
    )
    refusals = sorted(set(refusals))
    if refusals:
        standing = "REFUSED"
    elif remaining:
        standing = "PARTIAL_ALIVE"
    else:
        standing = "ALIVE"
    payload = {
        "schema": SCHEMA,
        "release": closure.get("release"),
        "normative_ledger": closure.get("normative_ledger"),
        "standing": standing,
        "refusals": refusals,
        "remaining": list(remaining),
        "subjects": sorted(
            f"{r.get('subject_id')}={r.get('repository')}@{r.get('sha')}" for r in rows
        ),
        "authority": "NONE",
    }
    payload["receipt_digest"] = canonical_digest(payload)
    return Verdict(standing, tuple(refusals), remaining, payload)


def evaluate_path(path: str | Path) -> Verdict:
    return evaluate(json.loads(Path(path).read_text(encoding="utf-8")))
