from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class EngineWitness:
    engine:str; implementation:str; model:str; semantic_digest:str; trace_digest:str; obligation_digest:str
def require_engines(witnesses):
    triples={(w.implementation,w.model) for w in witnesses}
    digests={(w.semantic_digest,w.trace_digest,w.obligation_digest) for w in witnesses}
    if len(triples)<2: raise Refused("INSUFFICIENT_ENGINE_INDEPENDENCE")
    if len(digests)!=1: raise Refused("ENGINE_CORRESPONDENCE_DIVERGENCE")
    return True
@dataclass(frozen=True)
class OracleWitness:
    kind:str; implementation:str; model:str; digest:str
def require_oracles(witnesses):
    by={w.kind:w for w in witnesses}
    if not {"POWL","OCEL"}<=set(by): raise Refused("MISSING_INDEPENDENT_ORACLE")
    if (by["POWL"].implementation,by["POWL"].model)==(by["OCEL"].implementation,by["OCEL"].model): raise Refused("ORACLE_COLLUSION")
    return True
