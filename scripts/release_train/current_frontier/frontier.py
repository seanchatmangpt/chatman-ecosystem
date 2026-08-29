from __future__ import annotations

from dataclasses import dataclass
from .evidence import Evidence
from .supersession import Supersession, validate_relations

@dataclass(frozen=True)
class Frontier:
    current: tuple[Evidence, ...]
    historical: tuple[Evidence, ...]

def resolve_frontier(evidence: tuple[Evidence, ...], relations: tuple[Supersession, ...]) -> Frontier:
    validate_relations(evidence, relations)
    superseded = {r.older_id for r in relations}
    current = tuple(sorted((e for e in evidence if e.evidence_id not in superseded), key=lambda e: e.evidence_id))
    historical = tuple(sorted((e for e in evidence if e.evidence_id in superseded), key=lambda e: e.evidence_id))
    return Frontier(current=current, historical=historical)

def standing(frontier: Frontier) -> str:
    outcomes={e.outcome for e in frontier.current}
    if "FAIL" in outcomes:
        return "BUILD_BROKEN"
    if "PENDING" in outcomes or "UNKNOWN" in outcomes or not outcomes:
        return "UNKNOWN"
    if outcomes == {"UNSUPPORTED"}:
        return "UNSUPPORTED"
    if outcomes <= {"PASS", "UNSUPPORTED"} and "PASS" in outcomes:
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
