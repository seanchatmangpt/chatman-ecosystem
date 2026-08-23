from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class CusumResult:
    max_positive: float
    max_negative: float
    drifted: bool
def two_sided_cusum(errors,reference=0.05,threshold=0.5):
    if reference<0 or threshold<=0: raise Refused("REFUSED[INVALID_CUSUM_POLICY]")
    pos=neg=maxpos=maxneg=0.0
    for raw in errors:
        e=float(raw); pos=max(0.0,pos+e-reference); neg=max(0.0,neg-e-reference); maxpos=max(maxpos,pos); maxneg=max(maxneg,neg)
    return CusumResult(maxpos,maxneg,maxpos>=threshold or maxneg>=threshold)
