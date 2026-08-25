from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True, order=True)
class IndependenceProof:
    left: str
    right: str
    basis: str
    def __post_init__(self):
        if not self.left or not self.right or self.left==self.right:
            raise Refused("REFUSED[INVALID_INDEPENDENCE_PROOF]")
        if not self.basis.strip():
            raise Refused("REFUSED[EMPTY_INDEPENDENCE_BASIS]")

def independent(candidate, selected, proofs):
    if not selected: return True
    pairs={frozenset((p.left,p.right)) for p in proofs}
    for other in selected:
        if candidate.sensor_family==other.sensor_family or candidate.implementation_domain==other.implementation_domain:
            return False
        if frozenset((candidate.candidate_id,other.candidate_id)) not in pairs:
            return False
    return True
