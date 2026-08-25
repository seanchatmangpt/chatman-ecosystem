from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True,order=True)
class Candidate:
    candidate_id:str
    worst_risk:Fraction
    false_stable:Fraction
    calibration_mae:Fraction
    cost:Fraction
def dominates(a,b):
    av=(a.worst_risk,a.false_stable,a.calibration_mae,a.cost); bv=(b.worst_risk,b.false_stable,b.calibration_mae,b.cost)
    return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))
def frontier(candidates):
    rows=tuple(candidates); return tuple(sorted(c for c in rows if not any(dominates(o,c) for o in rows if o!=c)))
def frontier_jaccard(before,after):
    a={c.candidate_id for c in before}; b={c.candidate_id for c in after}; u=a|b
    return Fraction(len(a&b),len(u)) if u else Fraction(1)
