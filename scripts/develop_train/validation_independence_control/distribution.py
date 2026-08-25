from dataclasses import dataclass
from datetime import datetime
from .errors import Refused
@dataclass(frozen=True)
class RegionWitness:
    host: str
    region: str
    generation: int
    semantic_digest: str
    observed_at: datetime
    expires_at: datetime
    encrypted: bool
    certificate_digest: str
def require_distribution(witnesses, now):
    xs=list(witnesses)
    if len({x.host for x in xs})<2 or len({x.region for x in xs})<2: raise Refused("INSUFFICIENT_DISTRIBUTION")
    if any(not (x.observed_at <= now < x.expires_at) for x in xs): raise Refused("STALE_REGION_EVIDENCE")
    if any(not x.encrypted or len(x.certificate_digest)!=64 for x in xs): raise Refused("TLS_EVIDENCE_INVALID")
    if len({(x.generation,x.semantic_digest) for x in xs})!=1: raise Refused("REGION_DIVERGENCE")
    return True
