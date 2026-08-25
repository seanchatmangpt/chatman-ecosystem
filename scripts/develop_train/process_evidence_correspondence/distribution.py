from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class RegionWitness:
    host:str; region:str; generation:int; observed_at:int; expires_at:int; encrypted:bool; certificate_digest:str; semantic_digest:str
    def current(self,now): return self.observed_at<=now<self.expires_at
def require_distribution(ws,now):
    if len({w.host for w in ws})<2 or len({w.region for w in ws})<2: raise Refused("INSUFFICIENT_DISTRIBUTION")
    if any(not w.current(now) for w in ws): raise Refused("STALE_REGION_EVIDENCE")
    if any(not w.encrypted or len(w.certificate_digest)!=64 for w in ws): raise Refused("TLS_CORRESPONDENCE_FAILURE")
    if len({w.generation for w in ws})!=1 or len({w.semantic_digest for w in ws})!=1: raise Refused("REGION_DIVERGENCE")
    return True
