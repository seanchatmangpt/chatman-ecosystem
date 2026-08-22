from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from .detector_vote import DetectorVote, canonical_votes

@dataclass(frozen=True)
class IndependenceProof:
    detector_a: str
    detector_b: str
    basis: str

    def pair(self) -> frozenset[str]:
        return frozenset((self.detector_a, self.detector_b))

def independent_clique(votes: list[DetectorVote], proofs: list[IndependenceProof]) -> tuple[DetectorVote, ...]:
    ordered = canonical_votes(votes)
    proven = {p.pair() for p in proofs if p.basis.strip()}
    chosen: list[DetectorVote] = []
    for vote in ordered:
        if all(vote.family != prior.family and vote.implementation_domain != prior.implementation_domain and frozenset((vote.name, prior.name)) in proven for prior in chosen):
            chosen.append(vote)
    return tuple(chosen)

def missing_pairs(votes: tuple[DetectorVote, ...], proofs: list[IndependenceProof]) -> tuple[tuple[str, str], ...]:
    proven = {p.pair() for p in proofs if p.basis.strip()}
    return tuple((a.name,b.name) for a,b in combinations(votes,2) if frozenset((a.name,b.name)) not in proven)
