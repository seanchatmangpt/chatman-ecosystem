from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

ORDER=("narrow","compile","unit","property","integration","e2e","replay","negative","security","exact_head_ci")

class LadderRefusal(ValueError):
    pass

@dataclass(frozen=True)
class Gate:
    name: str
    status: str

def evaluate(gates: Iterable[Gate]) -> str:
    rows={g.name:g.status for g in gates}
    unknown=set(rows)-set(ORDER)
    if unknown:
        raise LadderRefusal("REFUSED[UNKNOWN_VERIFICATION_GATE]")
    if any(rows.get(name) in {"failure","cancelled"} for name in ORDER):
        return "BUILD_BROKEN"
    first_missing=next((name for name in ORDER if rows.get(name)!="success"),None)
    if first_missing is not None:
        return "PARTIAL_ALIVE" if rows else "UNKNOWN"
    return "ALIVE"
