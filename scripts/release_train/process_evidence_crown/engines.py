from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class EngineWitness:
    rail:str; engine_id:str; implementation_digest:str; trace_digest:str; subject_key:str

def require_multi_engine(items):
    if len(items)<2: raise Refused("INSUFFICIENT_ENGINE_WITNESSES")
    if len({x.engine_id for x in items})<2 or len({x.implementation_digest for x in items})<2: raise Refused("ENGINE_WITNESSES_NOT_INDEPENDENT")
    if len({(x.subject_key,x.trace_digest) for x in items})!=1: raise Refused("ENGINE_TRACE_DIVERGENCE")
    return True
