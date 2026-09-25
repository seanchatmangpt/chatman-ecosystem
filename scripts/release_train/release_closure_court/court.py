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
LINEAGE_STATES = frozenset({"OPEN", "MERGED", "CLOSED_UNMERGED"})
LINEAGE_DISPOSITIONS = frozenset({"CANONICAL", "SUPERSEDED", "UNRESOLVED", "ZOMBIE", "CLOSED"})
_NON_TERMINAL = {"BLOCKED", "UNSUPPORTED", "REFUSED"}

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
    # Lineage laws (optional row ``lineage`` / ``depends_on``, closure ``max_canonical_additions``):
    # exactly one admitted head per subject, no open alternative realities.
    "REFUSED:SUCCESSOR_AMBIGUOUS",
    "REFUSED:CANONICAL_SUBJECT_SPLIT",
    "REFUSED:SUPERSEDED_LINEAGE_OPEN",
    "REFUSED:ALIVE_ON_NON_FINAL_HEAD",
    "REFUSED:SCOPE_EXCEEDS_BOUND",
    "REFUSED:DEPENDENCY_NOT_ADMITTED",
    "REFUSED:DEPENDENCY_CYCLE",
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


def _lineage_refusals(row: dict[str, Any], bound: int | None) -> list[str]:
    """PR lineage of a row: one CANONICAL head at the row sha, no open alternatives.

    Each entry: {pr, sha, state, draft, mergeable, disposition, additions?}. A row
    without ``lineage`` is unaffected.
    """
    sid = row.get("subject_id", "?")
    lineage = row.get("lineage")
    if lineage is None:
        return []
    if not isinstance(lineage, list):
        return [f"REFUSED:MALFORMED_ROW:{sid}:lineage"]
    out: list[str] = []
    canonical = []
    for pos, pr in enumerate(lineage):
        if (
            not isinstance(pr, dict)
            or not isinstance(pr.get("pr"), int)
            or isinstance(pr.get("pr"), bool)
            or not _SHA40.fullmatch(str(pr.get("sha", "")))
            or pr.get("state") not in LINEAGE_STATES
            or pr.get("disposition") not in LINEAGE_DISPOSITIONS
        ):
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:lineage[{pos}]")
            continue
        n = pr["pr"]
        if pr["disposition"] == "CANONICAL":
            canonical.append(pr)
            if pr["sha"] != row.get("sha"):
                out.append(f"REFUSED:CANONICAL_SUBJECT_SPLIT:{sid}:pr={n}")
            additions = pr.get("additions", 0)
            if bound is not None and isinstance(additions, int) and additions > bound:
                out.append(f"REFUSED:SCOPE_EXCEEDS_BOUND:{sid}:pr={n}:additions={additions}>{bound}")
        elif pr["state"] == "OPEN":
            if pr["disposition"] in {"SUPERSEDED", "ZOMBIE"}:
                out.append(f"REFUSED:SUPERSEDED_LINEAGE_OPEN:{sid}:pr={n}")
            else:
                out.append(f"REFUSED:SUCCESSOR_AMBIGUOUS:{sid}:pr={n}")
    if len(canonical) > 1:
        out.append(f"REFUSED:SUCCESSOR_AMBIGUOUS:{sid}:canonical={len(canonical)}")
    if row.get("impl_standing") == "ALIVE":
        for pr in canonical:
            if pr["state"] != "MERGED":
                out.append(
                    f"REFUSED:ALIVE_ON_NON_FINAL_HEAD:{sid}:pr={pr['pr']}:state={pr['state']}"
                    f":draft={bool(pr.get('draft'))}:mergeable={pr.get('mergeable', 'UNKNOWN')}"
                )
    return out


def _dependency_refusals(rows: list[dict[str, Any]]) -> list[str]:
    ids = {r.get("subject_id") for r in rows}
    out: list[str] = []
    graph: dict[str, list[str]] = {}
    for row in rows:
        sid = row.get("subject_id")
        deps = row.get("depends_on", [])
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:depends_on")
            continue
        for dep in deps:
            if dep not in ids or dep == sid:
                out.append(f"REFUSED:DEPENDENCY_NOT_ADMITTED:{sid}:{dep}")
        graph[sid] = [d for d in deps if d in ids and d != sid]
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        state[node] = 1
        for dep in graph.get(node, []):
            if state.get(dep) == 1:
                out.append(f"REFUSED:DEPENDENCY_CYCLE:{node}->{dep}")
            elif dep not in state:
                visit(dep)
        state[node] = 2

    for node in sorted(graph, key=str):
        if node not in state:
            visit(node)
    return out


def repair_order(rows: list[dict[str, Any]], remaining_ids: set[str]) -> list[str]:
    """Rows that still carry a typed blocker, dependencies first.

    Ties break by criticality: the subject that more rows (transitively) depend on
    is repaired first, then by subject_id.
    """
    graph: dict[str, list[str]] = {}
    for r in rows:
        deps = r.get("depends_on", [])
        graph[r.get("subject_id")] = [d for d in deps if isinstance(d, str)] if isinstance(deps, list) else []
    dependents: dict[str, set[str]] = {}
    for sid, deps in graph.items():
        for dep in deps:
            dependents.setdefault(dep, set()).add(sid)

    def reach(sid: str) -> int:
        seen: set[str] = set()
        stack = list(dependents.get(sid, ()))
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(dependents.get(node, ()))
        return len(seen)

    weight = {sid: reach(sid) for sid in remaining_ids}
    order: list[str] = []
    done: set[str] = set()
    while len(done) < len(remaining_ids):
        ready = [
            sid
            for sid in remaining_ids
            if sid not in done and all(d in done or d not in remaining_ids for d in graph.get(sid, []))
        ]
        if not ready:  # a cycle is refused elsewhere; emit the rest deterministically
            ready = [sid for sid in remaining_ids if sid not in done]
        nxt = min(ready, key=lambda sid: (-weight[sid], str(sid)))
        order.append(nxt)
        done.add(nxt)
    return order


def evaluate(closure: dict[str, Any]) -> Verdict:
    rows = closure.get("subjects", [])
    refusals: list[str] = []
    if not rows:
        refusals.append("REFUSED:MALFORMED_ROW:closure:subjects-empty")
    ids = [r.get("subject_id") for r in rows]
    for dup in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        refusals.append(f"REFUSED:DUPLICATE_SUBJECT_ID:{dup}")
    bound = closure.get("max_canonical_additions")
    if bound is not None and (not isinstance(bound, int) or isinstance(bound, bool) or bound < 0):
        refusals.append("REFUSED:MALFORMED_ROW:closure:max_canonical_additions")
        bound = None
    for row in rows:
        refusals.extend(_row_refusals(row))
        refusals.extend(_lineage_refusals(row, bound))
    refusals.extend(_dependency_refusals(rows))

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
    if any("depends_on" in r for r in rows):
        # Present only when the closure declares edges, so existing receipts keep their digest.
        payload["repair_order"] = repair_order(rows, {
            r.get("subject_id")
            for r in rows
            if r.get("spec_standing") in _NON_TERMINAL or r.get("impl_standing") in _NON_TERMINAL
        })
    payload["receipt_digest"] = canonical_digest(payload)
    return Verdict(standing, tuple(refusals), remaining, payload)


def evaluate_path(path: str | Path) -> Verdict:
    return evaluate(json.loads(Path(path).read_text(encoding="utf-8")))
