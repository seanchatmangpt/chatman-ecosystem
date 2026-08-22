from __future__ import annotations
from dataclasses import dataclass
import hashlib
from .subject import Refusal
@dataclass(frozen=True,slots=True)
class EvidenceSource:
    source_id:str; producer:str; run_id:str; artifact_id:str; family:str
    def __post_init__(self)->None:
        if not all((self.source_id,self.producer,self.run_id,self.artifact_id,self.family)): raise Refusal("REFUSED[INCOMPLETE_EVIDENCE_SOURCE]")
    @property
    def fingerprint(self)->str:
        return hashlib.sha256("|".join((self.source_id,self.producer,self.run_id,self.artifact_id,self.family)).encode()).hexdigest()
@dataclass(frozen=True,slots=True)
class IndependenceProof:
    left:str; right:str; independent:bool
def relation(a:EvidenceSource,b:EvidenceSource,proofs:tuple[IndependenceProof,...]=())->str:
    if a.fingerprint==b.fingerprint: return "SAME"
    if a.family==b.family or a.producer==b.producer or a.run_id==b.run_id or a.artifact_id==b.artifact_id: return "CORRELATED"
    pair={a.fingerprint,b.fingerprint}
    for proof in proofs:
        if {proof.left,proof.right}==pair: return "INDEPENDENT" if proof.independent else "CORRELATED"
    return "UNKNOWN"
def independent_cluster_count(sources:tuple[EvidenceSource,...],proofs:tuple[IndependenceProof,...])->int:
    chosen:list[EvidenceSource]=[]
    for candidate in sorted(sources,key=lambda s:s.fingerprint):
        if all(relation(candidate,existing,proofs)=="INDEPENDENT" for existing in chosen): chosen.append(candidate)
    return len(chosen)
