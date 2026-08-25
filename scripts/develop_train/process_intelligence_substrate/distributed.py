from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from .errors import Refused

@dataclass(frozen=True, order=True)
class RegionWitness:
    region: str
    semantic_digest: str
    observed_at: datetime


def require_current_agreement(witnesses: tuple[RegionWitness, ...], now: datetime, max_age: timedelta) -> str:
    if now.tzinfo is None or now.utcoffset() is None:
        raise Refused("NAIVE_CURRENT_TIME")
    if len(witnesses) < 2:
        raise Refused("MULTI_REGION_SUPPORT")
    digests = {w.semantic_digest for w in witnesses}
    if len(digests) != 1:
        raise Refused("MULTI_REGION_DIVERGENCE")
    for witness in witnesses:
        if witness.observed_at.tzinfo is None or now.astimezone(timezone.utc) - witness.observed_at.astimezone(timezone.utc) > max_age:
            raise Refused("STALE_REGION_WITNESS", witness.region)
    return next(iter(digests))
