from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .support import importance_weight
from .evidence import admit_log
@dataclass(frozen=True, slots=True)
class Interval:
    lower:Fraction; upper:Fraction
    def __post_init__(self):
        if self.lower > self.upper: raise Refused('REFUSED_INTERVAL_ORDER')
    @property
    def width(self): return self.upper-self.lower
def gamma_interval(rows,gamma):
    if gamma < 1: raise Refused('REFUSED_GAMMA_LT_ONE')
    rows=admit_log(rows); vals=[(importance_weight(r)*r.reward/gamma,importance_weight(r)*r.reward*gamma) for r in rows]
    return Interval(sum((a for a,_ in vals),Fraction())/len(rows),sum((b for _,b in vals),Fraction())/len(rows))
def breakdown_gamma(rows,threshold,grid=(Fraction(1),Fraction(5,4),Fraction(3,2),Fraction(2),Fraction(3))):
    for g in grid:
        iv=gamma_interval(rows,g)
        if iv.lower <= threshold <= iv.upper: return g
    return None
