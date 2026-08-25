from dataclasses import dataclass
from .errors import Refused
ENGINES=frozenset({"BEAM","PLAN","WASM","NIF","REMOTE"})
@dataclass(frozen=True)
class EngineWitness:
    engine:str; implementation:str; semantic_digest:str; trace_digest:str; obligation_digest:str
def require_engine_correspondence(ws,min_engines=2):
    if len(ws)<min_engines: raise Refused("INSUFFICIENT_ENGINE_WITNESSES")
    if any(w.engine not in ENGINES for w in ws): raise Refused("INVALID_ENGINE")
    if len({w.engine for w in ws})<min_engines or len({w.implementation for w in ws})<min_engines: raise Refused("ENGINE_ALIAS")
    for attr,code in [("semantic_digest","SEMANTIC_DIVERGENCE"),("trace_digest","TRACE_DIVERGENCE"),("obligation_digest","OBLIGATION_DIVERGENCE")]:
        if len({getattr(w,attr) for w in ws})!=1: raise Refused(code)
    return True
