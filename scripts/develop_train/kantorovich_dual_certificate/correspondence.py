from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class EngineWitness:
    engine: str; implementation: str; model: str; semantic: str; trace: str; obligation: str
@dataclass(frozen=True)
class OracleWitness:
    methodology: str; oracle: str; implementation: str; model: str; digest: str
def require_engines(witnesses):
    witnesses = tuple(witnesses)
    if len({w.engine for w in witnesses}) < 2 or len({w.implementation for w in witnesses}) < 2 or len({w.model for w in witnesses}) < 2:
        raise Refused("INSUFFICIENT_ENGINE_INDEPENDENCE")
    if len({(w.semantic, w.trace, w.obligation) for w in witnesses}) != 1:
        raise Refused("ENGINE_CORRESPONDENCE_DIVERGENCE")
    return True
def require_oracles(witnesses, methodology):
    selected = [w for w in witnesses if w.methodology == methodology]
    if len(selected) < 2 or len({w.implementation for w in selected}) < 2 or len({w.model for w in selected}) < 2:
        raise Refused("ORACLE_ALIAS")
    if len({w.digest for w in selected}) != 1:
        raise Refused("ORACLE_DIVERGENCE")
    return True
