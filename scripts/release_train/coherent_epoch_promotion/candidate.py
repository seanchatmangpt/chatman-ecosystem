from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class Persistence(str, Enum):
    MEMORY='MEMORY'; JSONL='JSONL'; SQLITE='SQLITE'

@dataclass(frozen=True)
class PromotionCandidate:
    persistence: Persistence
    transactional: bool
    reversible: bool = True

def candidates() -> tuple[PromotionCandidate, ...]:
    return (
        PromotionCandidate(Persistence.MEMORY, False),
        PromotionCandidate(Persistence.JSONL, False),
        PromotionCandidate(Persistence.SQLITE, True),
    )

def select_candidate(require_transactional: bool) -> PromotionCandidate:
    viable = [c for c in candidates() if c.reversible and (not require_transactional or c.transactional)]
    if not viable: raise ValueError('REFUSED[NO_REVERSIBLE_CANDIDATE]')
    return viable[0]
