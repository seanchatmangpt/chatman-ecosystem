from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True, order=True)
class IndependenceProof:
    left: str
    right: str
    proof_id: str
    def __post_init__(self):
        if not self.left or not self.right or self.left==self.right or not self.proof_id:
            raise Refused("REFUSED[INVALID_INDEPENDENCE_PROOF]")

def require_independent(a,b,proofs):
    if a.implementation_digest==b.implementation_digest: raise Refused("REFUSED[SHARED_IMPLEMENTATION]")
    if a.model_digest and a.model_digest==b.model_digest: raise Refused("REFUSED[SHARED_MODEL]")
    keys={frozenset((p.left,p.right)) for p in proofs}
    if frozenset((a.estimator_id,b.estimator_id)) not in keys: raise Refused("REFUSED[INDEPENDENCE_UNPROVEN]")
    return True
