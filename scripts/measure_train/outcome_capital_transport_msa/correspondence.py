from dataclasses import dataclass
from datetime import datetime
from .subject import Refused
@dataclass(frozen=True,order=True)
class EngineWitness:
    engine:str
    implementation_digest:str
    model_digest:str
    semantic_digest:str
    trace_digest:str
    obligation_digest:str
@dataclass(frozen=True,order=True)
class RegionWitness:
    host:str
    region:str
    semantic_digest:str
    encrypted:bool
    certificate_digest:str
    observed_at:datetime
def require_engines(rows):
    rows=tuple(rows)
    if len(rows)<2: raise Refused("REFUSED[INSUFFICIENT_ENGINE_WITNESSES]")
    if len({r.implementation_digest for r in rows})<2 or len({r.model_digest for r in rows})<2:
        raise Refused("REFUSED[NONINDEPENDENT_ENGINE_WITNESSES]")
    if len({(r.semantic_digest,r.trace_digest,r.obligation_digest) for r in rows})!=1:
        raise Refused("REFUSED[ENGINE_CORRESPONDENCE_DIVERGENCE]")
    return True
def require_regions(rows,now,ttl_seconds=3600):
    rows=tuple(rows)
    if len({r.host for r in rows})<2 or len({r.region for r in rows})<2:
        raise Refused("REFUSED[INSUFFICIENT_MULTI_REGION_WITNESSES]")
    if any(not r.encrypted or len(r.certificate_digest)!=64 for r in rows):
        raise Refused("REFUSED[UNPROVEN_TLS_CORRESPONDENCE]")
    if any((now-r.observed_at).total_seconds()<0 or (now-r.observed_at).total_seconds()>ttl_seconds for r in rows):
        raise Refused("REFUSED[STALE_REGION_WITNESS]")
    if len({r.semantic_digest for r in rows})!=1:
        raise Refused("REFUSED[REGION_SEMANTIC_DIVERGENCE]")
    return True
