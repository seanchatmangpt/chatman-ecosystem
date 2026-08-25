from dataclasses import dataclass
from datetime import datetime
from .subject import Refused
@dataclass(frozen=True)
class RegionWitness:
    region:str; host_id:str; semantic_digest:str; observed_at:datetime; encrypted:bool
def multi_region_current(witnesses, now, ttl_seconds):
    rows=tuple(witnesses)
    for w in rows:
        if w.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_REGION_TIME]")
        if (now-w.observed_at).total_seconds()>ttl_seconds: raise Refused("REFUSED[STALE_REGION_WITNESS]")
        if not w.encrypted: raise Refused("REFUSED[UNENCRYPTED_DISTRIBUTED_WITNESS]")
    if len({w.region for w in rows})<2 or len({w.host_id for w in rows})<2: raise Refused("REFUSED[NONINDEPENDENT_REGIONS]")
    if len({w.semantic_digest for w in rows})!=1: raise Refused("REFUSED[REGION_SEMANTIC_DIVERGENCE]")
    return "CURRENT"
