from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class EngineWitness:
    engine:str; implementation:str; trace_digest:str
def require_differential(witnesses):
    ws=list(witnesses)
    if len({w.implementation for w in ws})<2: raise Refused("INSUFFICIENT_ENGINE_INDEPENDENCE")
    if len({w.trace_digest for w in ws})!=1: raise Refused("ENGINE_TRACE_DIVERGENCE")
    return True
