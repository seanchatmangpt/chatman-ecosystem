from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject

class CandidateRefusal(ValueError):
    pass

@dataclass(frozen=True)
class PromotionCandidate:
    candidate_id: str
    root: Subject
    benefit: int
    reversibility: int
    dependency_relief: int
    risk: int

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise CandidateRefusal("REFUSED[EMPTY_CANDIDATE_ID]")
        for value in (self.benefit, self.reversibility, self.dependency_relief, self.risk):
            if not 0 <= value <= 100:
                raise CandidateRefusal("REFUSED[UNBOUNDED_CANDIDATE_SCORE]")

    @property
    def score(self) -> int:
        return self.benefit + self.reversibility + self.dependency_relief - self.risk

def preserve_frontier(candidates: list[PromotionCandidate]) -> tuple[PromotionCandidate, ...]:
    viable = [c for c in candidates if c.reversibility > 0]
    return tuple(sorted(viable, key=lambda c: (-c.score, c.candidate_id)))
