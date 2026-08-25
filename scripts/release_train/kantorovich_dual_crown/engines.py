from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class EngineWitness:
    rail:str; implementation:str; model:str; semantic_digest:str; trace_digest:str; obligation_digest:str
def require_engines(xs):
    if len(xs)<2: raise Refused("INSUFFICIENT_ENGINES")
    if len({x.implementation for x in xs})<2 or len({x.model for x in xs})<2: raise Refused("ENGINE_NOT_INDEPENDENT")
    triples={(x.semantic_digest,x.trace_digest,x.obligation_digest) for x in xs}
    if len(triples)!=1: raise Refused("ENGINE_CORRESPONDENCE_DIVERGENCE")
    return True
