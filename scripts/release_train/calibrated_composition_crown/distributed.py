from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class RegionEvidence:
    host:str; region:str; generation:int; encrypted:bool; certificate_digest:str
def require_current_tls(xs,generation):
    xs=list(xs)
    if len({x.host for x in xs})<2 or len({x.region for x in xs})<2: raise Refused("INSUFFICIENT_MULTI_REGION_EVIDENCE")
    if any(x.generation!=generation for x in xs): raise Refused("STALE_DISTRIBUTED_EVIDENCE")
    if any(not x.encrypted or len(x.certificate_digest)!=64 for x in xs): raise Refused("TLS_SECURITY_CORRESPONDENCE")
    return True
