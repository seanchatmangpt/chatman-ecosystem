from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .graph import Edge, dependency_closure

class SelectionRefusal(ValueError):
    pass

@dataclass(frozen=True)
class Candidate:
    key: str
    repo: str
    value: int
    reversibility: int
    evidence: int
    release_criticality: int
    blocked: bool=False

    @property
    def score(self) -> tuple[int,int,int,int,str]:
        return (self.release_criticality,self.evidence,self.value,self.reversibility,self.key)

def select(candidates: Iterable[Candidate], edges: Iterable[Edge]) -> tuple[Candidate, tuple[str,...]]:
    viable=[c for c in candidates if not c.blocked]
    if not viable:
        raise SelectionRefusal("BLOCKED[NO_IMPLEMENTABLE_IMPLEMENT_TICKET]")
    chosen=max(viable,key=lambda c:c.score)
    return chosen, dependency_closure(chosen.repo,edges)
