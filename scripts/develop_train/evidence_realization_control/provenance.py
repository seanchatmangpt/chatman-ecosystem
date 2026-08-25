from dataclasses import dataclass
from .evidence import EvidenceNode
from .errors import Refused
@dataclass(frozen=True)
class ProvenanceWitness:
    left:str
    right:str

def require_distinct_provenance(a:EvidenceNode,b:EvidenceNode):
    if a.implementation==b.implementation or a.model==b.model or a.domain==b.domain:
        raise Refused('REFUSED[DEPENDENT_EVIDENCE]')
    return ProvenanceWitness(a.evidence_id,b.evidence_id)
