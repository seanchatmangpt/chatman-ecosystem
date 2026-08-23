from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class RegionWitness:
    host:str; region:str; encrypted:bool; certificate_digest:str; generation:int
def require_regions(items,current_generation):
    current=[x for x in items if x.generation==current_generation]
    if len({x.host for x in current})<2 or len({x.region for x in current})<2: raise Refused("INSUFFICIENT_MULTI_REGION")
    if any(not x.encrypted or not x.certificate_digest for x in current): raise Refused("TLS_CORRESPONDENCE_FAILURE")
    return True
