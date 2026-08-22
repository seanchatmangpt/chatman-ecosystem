from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from .evidence import Evidence
from .window import parse_time

@dataclass(frozen=True)
class Invalidation:
    source_id: str
    reason: str

def detect_invalidations(rows: tuple[Evidence,...], now: datetime, ttl_by_kind: dict[str,timedelta])->tuple[Invalidation,...]:
    now=parse_time(now); out=[]
    for row in rows:
        ttl=ttl_by_kind.get(str(row.kind))
        if ttl is not None and now-row.observed_at > ttl: out.append(Invalidation(row.source_id,"TTL_EXPIRED"))
    return tuple(sorted(out,key=lambda x:(x.source_id,x.reason)))
