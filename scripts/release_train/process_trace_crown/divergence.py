from __future__ import annotations
from dataclasses import dataclass
from .trace import Trace

@dataclass(frozen=True)
class Divergence:
    index: int
    left: object | None
    right: object | None

def minimal(left: Trace, right: Trace) -> Divergence | None:
    n = max(len(left.events), len(right.events))
    for i in range(n):
        le = left.events[i] if i < len(left.events) else None
        re = right.events[i] if i < len(right.events) else None
        if le != re:
            return Divergence(i, le, re)
    return None
