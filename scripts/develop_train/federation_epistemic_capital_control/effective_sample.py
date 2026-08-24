from dataclasses import dataclass
from fractions import Fraction
from .linear import inverse
from .errors import Refused
@dataclass(frozen=True)
class EffectiveSample: nominal:int; generalized:Fraction; design_effect:Fraction
def generalized_ess(g):
    n=len(g.ids); inv=inverse(g.matrix); total=sum(inv[i][j] for i in range(n) for j in range(n))
    if total<=0: raise Refused("NONPOSITIVE_EFFECTIVE_SAMPLE")
    total=min(total,Fraction(n)); return EffectiveSample(n,total,Fraction(n)/total)
