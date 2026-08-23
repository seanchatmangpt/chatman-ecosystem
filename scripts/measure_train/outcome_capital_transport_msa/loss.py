from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused
@dataclass(frozen=True)
class LossMatrix:
    false_independent: Fraction
    false_dependent: Fraction
    defer: Fraction
    def __post_init__(self):
        if min(self.false_independent,self.false_dependent,self.defer)<0:
            raise Refused("REFUSED[NEGATIVE_LOSS]")
def realized_loss(o,matrix):
    if not o.labeled: raise Refused("REFUSED[UNLABELED_OUTCOME]")
    if o.decision=="DEFER": return matrix.defer
    if o.decision==o.truth: return Fraction(0)
    return matrix.false_independent if o.decision=="INDEPENDENT" else matrix.false_dependent
