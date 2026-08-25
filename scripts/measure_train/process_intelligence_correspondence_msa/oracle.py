from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class OracleWitness:
    oracle_id:str; implementation_digest:str; subject_sha:str; semantic_digest:str; verdict:str
def independent_agreement(witnesses):
    rows=tuple(witnesses)
    if len(rows)<2: raise Refused("REFUSED[INSUFFICIENT_ORACLES]")
    if len({w.implementation_digest for w in rows})<2: raise Refused("REFUSED[NONINDEPENDENT_ORACLES]")
    if len({w.subject_sha for w in rows})!=1 or len({w.semantic_digest for w in rows})!=1: raise Refused("REFUSED[ORACLE_SUBJECT_DRIFT]")
    return "AGREE" if len({w.verdict for w in rows})==1 else "DISAGREE"
