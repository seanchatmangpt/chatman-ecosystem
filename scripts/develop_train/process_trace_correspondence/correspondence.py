from dataclasses import dataclass
from .rail import Rail,index
from .errors import Refused
@dataclass(frozen=True)
class Correspondence:
    semantic_digest:str; trace_digest:str; rails:frozenset[Rail]
def admit(evidence,required=frozenset(Rail)):
    by=index(evidence); missing=set(required)-set(by)
    if missing: raise Refused("MISSING_RAIL:"+",".join(sorted(x.value for x in missing)))
    vals=list(by.values()); subjects={x.subject for x in vals}; sem={x.semantic_digest for x in vals}; traces={x.trace_digest for x in vals}
    if len(subjects)!=1: raise Refused("RAIL_SUBJECT_DIVERGENCE")
    if len(sem)!=1: raise Refused("RAIL_SEMANTIC_DIVERGENCE")
    if len(traces)!=1: raise Refused("RAIL_TRACE_DIVERGENCE")
    return Correspondence(next(iter(sem)),next(iter(traces)),frozenset(by))
