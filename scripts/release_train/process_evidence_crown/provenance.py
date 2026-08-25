from dataclasses import dataclass
from .evidence import EvidenceNode
from .refusal import Refused

@dataclass(frozen=True)
class ProvenanceWitness:
    left: str; right: str; implementation_distinct: bool; model_distinct: bool; domain_distinct: bool
    def admits(self): return self.implementation_distinct and self.model_distinct and self.domain_distinct

def require_distinct(a: EvidenceNode, b: EvidenceNode, witness: ProvenanceWitness):
    if {witness.left,witness.right}!={a.id,b.id}: raise Refused("FOREIGN_PROVENANCE_WITNESS")
    intrinsic=(a.implementation!=b.implementation and a.model!=b.model and a.domain!=b.domain)
    if not witness.admits() or not intrinsic: raise Refused("EVIDENCE_PROVENANCE_NOT_INDEPENDENT")
    return True
