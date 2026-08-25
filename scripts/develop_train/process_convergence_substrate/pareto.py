from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Candidate:
    name: str
    residual_debt: Fraction
    regression_hazard: Fraction
    blocker_count: int


def dominates(a: Candidate,b: Candidate) -> bool:
    av=(a.residual_debt,a.regression_hazard,a.blocker_count)
    bv=(b.residual_debt,b.regression_hazard,b.blocker_count)
    return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))


def frontier(candidates):
    cs=tuple(sorted(candidates,key=lambda c:c.name))
    return tuple(c for c in cs if not any(dominates(o,c) for o in cs if o is not c))
