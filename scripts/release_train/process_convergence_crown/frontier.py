from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Candidate:
    name: str
    debt: Fraction
    hazards: int
    blockers: int
    oscillations: int

def dominates(a: Candidate,b: Candidate) -> bool:
    av=(a.debt,a.hazards,a.blockers,a.oscillations); bv=(b.debt,b.hazards,b.blockers,b.oscillations)
    return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))

def pareto(candidates):
    xs=tuple(candidates)
    return tuple(c for c in xs if not any(dominates(o,c) for o in xs if o!=c))
