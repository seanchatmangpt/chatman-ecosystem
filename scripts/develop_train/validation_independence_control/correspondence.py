from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class EngineWitness:
    engine: str
    implementation: str
    semantic_digest: str
    trace_digest: str
    obligation_digest: str
def require_engine_correspondence(witnesses):
    xs=list(witnesses)
    if len({x.implementation for x in xs})<2: raise Refused("ENGINE_ALIAS")
    if len({(x.semantic_digest,x.trace_digest,x.obligation_digest) for x in xs})!=1:
        raise Refused("ENGINE_DIVERGENCE")
    return True
@dataclass(frozen=True)
class OracleWitness:
    family: str
    implementation: str
    model: str
    digest: str
def require_oracles(witnesses, family):
    xs=[x for x in witnesses if x.family==family]
    if len(xs)<2 or len({x.implementation for x in xs})<2 or len({x.model for x in xs})<2 or len({x.digest for x in xs})!=1:
        raise Refused("ORACLE_NOT_INDEPENDENT",family)
    return True
