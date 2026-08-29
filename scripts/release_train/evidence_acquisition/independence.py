from dataclasses import dataclass

from .candidate import EvidenceCandidate

@dataclass(frozen=True)
class IndependenceProof:
    left_id: str
    right_id: str

    def pair(self) -> tuple[str, str]:
        if self.left_id == self.right_id:
            raise ValueError("REFUSED[SELF_INDEPENDENCE_PROOF]")
        return tuple(sorted((self.left_id, self.right_id)))

def admitted_independent(left: EvidenceCandidate, right: EvidenceCandidate, proofs: tuple[IndependenceProof, ...]) -> bool:
    if left.id == right.id or left.family == right.family or left.domain == right.domain:
        return False
    target = tuple(sorted((left.id, right.id)))
    return target in {proof.pair() for proof in proofs}
