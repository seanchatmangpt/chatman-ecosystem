from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .evidence import Evidence, Outcome
from .identity import Standing

@dataclass(frozen=True)
class Census:
    total: int
    by_kind: dict[str,int]
    by_outcome: dict[str,int]
    standing: Standing

def census(rows: tuple[Evidence,...])->Census:
    kinds=Counter(str(r.kind) for r in rows); outcomes=Counter(str(r.outcome) for r in rows)
    if not rows: standing=Standing.UNKNOWN
    elif any(r.outcome==Outcome.FAIL for r in rows): standing=Standing.BUILD_BROKEN
    elif any(r.outcome in (Outcome.PENDING,Outcome.UNKNOWN) for r in rows): standing=Standing.UNKNOWN
    elif all(r.outcome==Outcome.UNSUPPORTED for r in rows): standing=Standing.UNSUPPORTED
    else: standing=Standing.PARTIAL_ALIVE
    return Census(len(rows),dict(sorted(kinds.items())),dict(sorted(outcomes.items())),standing)
