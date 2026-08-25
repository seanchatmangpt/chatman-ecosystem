from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class EngineWitness:
    engine: str
    implementation: str
    semantic_digest: str
    trace_digest: str
    obligation_digest: str

@dataclass(frozen=True)
class OracleWitness:
    oracle: str
    implementation: str
    model: str
    methodology: str
    digest: str

def require_engines(witnesses):
    ws = tuple(witnesses)
    if len({w.engine for w in ws}) < 2 or len({w.implementation for w in ws}) < 2:
        raise Refused("INSUFFICIENT_ENGINE_INDEPENDENCE")
    triples = {(w.semantic_digest, w.trace_digest, w.obligation_digest) for w in ws}
    if len(triples) != 1:
        raise Refused("ENGINE_CORRESPONDENCE_DIVERGENCE")
    return True

def require_oracles(witnesses, methodology):
    ws = [w for w in witnesses if w.methodology == methodology]
    if len(ws) < 2:
        raise Refused("INSUFFICIENT_ORACLE_SUPPORT")
    if len({w.implementation for w in ws}) < 2 or len({w.model for w in ws}) < 2:
        raise Refused("ORACLE_ALIAS")
    if len({w.digest for w in ws}) != 1:
        raise Refused("ORACLE_DIVERGENCE")
    return True
