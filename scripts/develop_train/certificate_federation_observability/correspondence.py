from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class EngineWitness: engine:str; implementation:str; semantic_digest:str; trace_digest:str; obligation_digest:str
@dataclass(frozen=True)
class OracleWitness: oracle:str; implementation:str; model:str; methodology:str; digest:str
def require_engines(ws):
    ws=tuple(ws)
    if len({w.engine for w in ws})<2 or len({w.implementation for w in ws})<2: raise Refused("ENGINE_ALIAS")
    if len({(w.semantic_digest,w.trace_digest,w.obligation_digest) for w in ws})!=1: raise Refused("ENGINE_DIVERGENCE")
    return True
def require_oracles(ws,methodology):
    xs=[w for w in ws if w.methodology==methodology]
    if len(xs)<2 or len({w.implementation for w in xs})<2 or len({w.model for w in xs})<2: raise Refused("ORACLE_ALIAS")
    if len({w.digest for w in xs})!=1: raise Refused("ORACLE_DIVERGENCE")
    return True
