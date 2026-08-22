from dataclasses import dataclass
from fractions import Fraction
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class Belief:
    defect:Fraction; generation:int
    def __post_init__(self):
        if self.defect<=0 or self.defect>=1 or self.generation<0: raise Refusal('REFUSED_INVALID_BELIEF')
def pass_probability(b,tpr,fpr): return 1-(b.defect*tpr+(1-b.defect)*fpr)
def posterior_defect(b,*,tpr,fpr,detects):
    p=b.defect
    den=p*(tpr if detects else 1-tpr)+(1-p)*(fpr if detects else 1-fpr)
    if den==0: raise Refusal('REFUSED_ZERO_PREDICTIVE_MASS')
    return p*(tpr if detects else 1-tpr)/den
