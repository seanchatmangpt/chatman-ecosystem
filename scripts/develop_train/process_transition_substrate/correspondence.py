from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class ProjectionWitness:
    engine:str
    semantic_digest:str
    obligations:frozenset[str]
    trace_digest:str
def require_equivalent(witnesses):
    ws=list(witnesses)
    if len({w.engine for w in ws})<2: raise Refused("REFUSED[ENGINE_INDEPENDENCE_REQUIRED]")
    if len({w.semantic_digest for w in ws})!=1: raise Refused("REFUSED[SEMANTIC_DIVERGENCE]")
    if len({w.obligations for w in ws})!=1: raise Refused("REFUSED[OBLIGATION_LOSS]")
    if len({w.trace_digest for w in ws})!=1: raise Refused("REFUSED[TRACE_DIVERGENCE]")
    return True
