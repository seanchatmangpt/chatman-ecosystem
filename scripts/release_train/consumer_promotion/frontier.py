from dataclasses import dataclass
from .evidence import ProducerEvidence
@dataclass(frozen=True)
class Frontier:
    current:ProducerEvidence|None
    diverged:bool
def resolve(evidence:list[ProducerEvidence])->Frontier:
    if not evidence: return Frontier(None,False)
    subjects={e.subject for e in evidence}
    if len(subjects)!=1: raise ValueError("REFUSED[FOREIGN_FRONTIER]")
    receipts={e.receipt for e in evidence}
    schemas={e.schema for e in evidence}
    if len(receipts)>1 or len(schemas)>1: return Frontier(None,True)
    return Frontier(evidence[0],False)
