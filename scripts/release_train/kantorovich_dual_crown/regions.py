from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class RegionWitness:
    host:str; region:str; encrypted:bool; certificate_digest:str; generation:int; current:bool=True
def require_regions(xs):
    ys=[x for x in xs if x.current and x.encrypted and len(x.certificate_digest)>=8]
    if len({x.host for x in ys})<2 or len({x.region for x in ys})<2: raise Refused("MULTI_REGION_TLS_GAP")
    if len({x.generation for x in ys})!=1: raise Refused("REGION_GENERATION_DIVERGENCE")
    return True
