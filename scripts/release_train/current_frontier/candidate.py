from __future__ import annotations

from dataclasses import dataclass
from .admission import Admission

class Refusal(ValueError):
    pass

@dataclass(frozen=True)
class Candidate:
    name: str
    admissions: tuple[Admission,...]
    dependency_relief: int
    reversibility: int
    risk: int

    @property
    def score(self) -> tuple[int,int,int,str]:
        return (self.dependency_relief, self.reversibility, -self.risk, self.name)

def select(candidates: tuple[Candidate,...]) -> Candidate:
    viable=[c for c in candidates if c.admissions and all(a.promotable for a in c.admissions)]
    if not viable:
        raise Refusal("REFUSED[NO_CURRENT_FRONTIER_CANDIDATE]")
    return sorted(viable, key=lambda c:c.score, reverse=True)[0]
