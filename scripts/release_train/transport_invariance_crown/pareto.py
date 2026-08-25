from dataclasses import dataclass
from .refusal import require

@dataclass(frozen=True, order=True)
class Candidate:
    name: str
    worst_risk: float
    minimum_support: float
    maximum_shift: float
    minimum_ess: float


def dominates(a: Candidate,b: Candidate) -> bool:
    no_worse=(a.worst_risk<=b.worst_risk and a.minimum_support>=b.minimum_support and a.maximum_shift<=b.maximum_shift and a.minimum_ess>=b.minimum_ess)
    strict=(a.worst_risk<b.worst_risk or a.minimum_support>b.minimum_support or a.maximum_shift<b.maximum_shift or a.minimum_ess>b.minimum_ess)
    return no_worse and strict

def frontier(candidates: tuple[Candidate,...]) -> tuple[Candidate,...]:
    require(bool(candidates),"NO_CANDIDATES")
    out=[c for c in candidates if not any(dominates(other,c) for other in candidates if other!=c)]
    return tuple(sorted(out,key=lambda c:c.name))

def select(candidates: tuple[Candidate,...],strategy:str) -> Candidate:
    f=frontier(candidates)
    keys={
      'MINIMAX': lambda c:(c.worst_risk,-c.minimum_ess,c.name),
      'MAX_SUPPORT': lambda c:(-c.minimum_support,c.worst_risk,c.name),
      'MIN_SHIFT': lambda c:(c.maximum_shift,c.worst_risk,c.name),
      'MAX_ESS': lambda c:(-c.minimum_ess,c.worst_risk,c.name),
      'BALANCED': lambda c:(c.worst_risk+c.maximum_shift-(c.minimum_support+c.minimum_ess)/2,c.name),
    }
    require(strategy in keys,"UNKNOWN_SELECTION_STRATEGY",strategy)
    return min(f,key=keys[strategy])
