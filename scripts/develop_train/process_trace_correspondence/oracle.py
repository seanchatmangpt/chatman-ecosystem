from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class OracleWitness:
    oracle_id:str; implementation_digest:str; subject:str; semantic_digest:str; trace_digest:str
def admit(a:OracleWitness,b:OracleWitness):
    if a.oracle_id==b.oracle_id or a.implementation_digest==b.implementation_digest: raise Refused("NON_INDEPENDENT_ORACLE")
    if a.subject!=b.subject: raise Refused("ORACLE_SUBJECT_MISMATCH")
    if a.semantic_digest!=b.semantic_digest: raise Refused("SEMANTIC_DIVERGENCE")
    if a.trace_digest!=b.trace_digest: raise Refused("TRACE_DIVERGENCE")
    return True
