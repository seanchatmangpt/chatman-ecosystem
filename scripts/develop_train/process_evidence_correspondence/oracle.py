from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class OracleWitness:
    family:str; implementation:str; model:str; semantic_digest:str; verdict_digest:str
def require_oracles(witnesses,families=("POWL","OCEL")):
    by={f:[] for f in families}
    for w in witnesses:
        if w.family in by: by[w.family].append(w)
    for f,ws in by.items():
        if len(ws)<2: raise Refused("INSUFFICIENT_ORACLE",f)
        impl={w.implementation for w in ws}; models={w.model for w in ws}; sem={w.semantic_digest for w in ws}; verdict={w.verdict_digest for w in ws}
        if len(impl)<2 or len(models)<2 or len(sem)!=1 or len(verdict)!=1: raise Refused("ORACLE_DIVERGENCE",f)
    return True
