from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True, order=True)
class EvidenceIdentity:
    estimator: str
    implementation_digest: str
    model_digest: str

@dataclass(frozen=True)
class IndependenceProof:
    pairs: frozenset[tuple[str, str]]
    def require(self, left: EvidenceIdentity, right: EvidenceIdentity):
        if left.implementation_digest == right.implementation_digest:
            raise Refused("SHARED_IMPLEMENTATION")
        if left.model_digest == right.model_digest:
            raise Refused("SHARED_MODEL")
        edge = tuple(sorted((left.estimator, right.estimator)))
        if edge not in self.pairs: raise Refused("UNPROVEN_INDEPENDENCE")
        return True
