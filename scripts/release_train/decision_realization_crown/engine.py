from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class EngineWitness:
    engine:str; implementation_digest:str; model_digest:str; semantic_digest:str; trace_digest:str
def require_engines(witnesses):
    w=tuple(witnesses)
    if len(w)<2: raise Refused("INSUFFICIENT_ENGINE_CORRESPONDENCE")
    if len({x.implementation_digest for x in w})<2 or len({x.model_digest for x in w})<2: raise Refused("ENGINE_COLLUSION")
    if len({x.semantic_digest for x in w})!=1 or len({x.trace_digest for x in w})!=1: raise Refused("ENGINE_DIVERGENCE")
    return True
