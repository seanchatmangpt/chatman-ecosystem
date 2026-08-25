from dataclasses import dataclass
from .errors import Refused
REQUIRED_RAILS=frozenset({'SEMANTIC','POWL','REACTOR','BEAM','PLAN','WASM','NIF','REMOTE','BRCE'})
@dataclass(frozen=True)
class EngineEvidence:
    name:str; implementation_digest:str; model_digest:str; trace_digest:str
def require_engines(engines):
    es=tuple(engines)
    if len(es)<2: raise Refused('MULTI_ENGINE_EVIDENCE_REQUIRED')
    if len({e.implementation_digest for e in es})<2: raise Refused('ENGINE_IMPLEMENTATION_COLLUSION')
    if len({e.model_digest for e in es})<2: raise Refused('ENGINE_MODEL_COLLUSION')
    if len({e.trace_digest for e in es})!=1: raise Refused('ENGINE_TRACE_DIVERGENCE')
    return True
def require_rails(rail_digests):
    if set(rail_digests)!=REQUIRED_RAILS: raise Refused('INCOMPLETE_RAIL_CORRESPONDENCE')
    if len(set(rail_digests.values()))!=1: raise Refused('RAIL_CORRESPONDENCE_DIVERGENCE')
    return True
