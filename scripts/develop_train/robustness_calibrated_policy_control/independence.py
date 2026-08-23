from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True, order=True)
class EvidenceIdentity:
    estimator:str
    implementation:str
    model:str
@dataclass(frozen=True)
class IndependenceProof:
    pairs:frozenset[frozenset[EvidenceIdentity]]
    def require(self, identities:tuple[EvidenceIdentity,...])->None:
        if len(set(identities))!=len(identities): raise Refused('DUPLICATE_EVIDENCE_IDENTITY')
        for i,a in enumerate(identities):
            for b in identities[i+1:]:
                if a.implementation==b.implementation or a.model==b.model: raise Refused('CORRELATED_EVIDENCE')
                if frozenset((a,b)) not in self.pairs: raise Refused('UNPROVEN_INDEPENDENCE')
