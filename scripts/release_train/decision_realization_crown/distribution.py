from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class RegionWitness:
    host:str; region:str; encrypted:bool; certificate_digest:str; current:bool
def require_distribution(witnesses):
    w=tuple(witnesses)
    if len({x.host for x in w})<2 or len({x.region for x in w})<2: raise Refused("INSUFFICIENT_DISTRIBUTION")
    if any(not x.current for x in w): raise Refused("STALE_REGION_EVIDENCE")
    if any(not x.encrypted or len(x.certificate_digest)!=64 for x in w): raise Refused("TLS_EVIDENCE_INVALID")
    return True
