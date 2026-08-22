from __future__ import annotations
from dataclasses import dataclass
from .detector_vote import DetectorVote
from .independence import IndependenceProof, independent_clique

@dataclass(frozen=True)
class Consensus:
    changed: bool
    agreeing: int
    admitted: int
    required: int
    detectors: tuple[str, ...]

def decide(votes: list[DetectorVote], proofs: list[IndependenceProof], required: int = 2) -> Consensus:
    if required < 2:
        raise ValueError("REFUSED[WEAK_CHANGE_QUORUM]")
    clique = independent_clique(votes, proofs)
    agreeing = sum(1 for vote in clique if vote.changed)
    return Consensus(agreeing >= required, agreeing, len(clique), required, tuple(v.name for v in clique))
