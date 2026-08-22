from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class DetectorVote:
    name: str
    family: str
    implementation_domain: str
    changed: bool
    score: float

    def __post_init__(self) -> None:
        if not self.name or not self.family or not self.implementation_domain:
            raise ValueError("REFUSED[INCOMPLETE_DETECTOR_PROVENANCE]")
        if self.score < 0:
            raise ValueError("REFUSED[NEGATIVE_DETECTOR_SCORE]")

def canonical_votes(votes: list[DetectorVote]) -> tuple[DetectorVote, ...]:
    ordered = tuple(sorted(votes, key=lambda v: v.name))
    if len({v.name for v in ordered}) != len(ordered):
        raise ValueError("REFUSED[DUPLICATE_DETECTOR_VOTE]")
    return ordered
