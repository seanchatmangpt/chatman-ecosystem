from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from .refusal import Refused

@dataclass(frozen=True)
class TimedEvidence:
    observed_at: datetime
    generation: int

def require_current(rows: tuple[TimedEvidence, ...], now: datetime, ttl: timedelta) -> int:
    if now.tzinfo is None:
        raise Refused("NAIVE_NOW")
    if not rows:
        raise Refused("NO_CURRENT_EVIDENCE")
    generations = {r.generation for r in rows}
    if len(generations) != 1:
        raise Refused("SPLIT_EVIDENCE_GENERATION")
    for row in rows:
        if row.observed_at.tzinfo is None:
            raise Refused("NAIVE_EVIDENCE_TIME")
        if row.observed_at > now:
            raise Refused("FUTURE_EVIDENCE")
        if now - row.observed_at > ttl:
            raise Refused("STALE_EVIDENCE")
    return next(iter(generations))
