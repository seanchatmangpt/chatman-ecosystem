from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from .subject import Refusal

@dataclass(frozen=True, slots=True)
class CusumResult:
    positive:Fraction; negative:Fraction; alarm:bool

def prequential_cusum(errors:tuple[int,...],*,target:Fraction,slack:Fraction,threshold:Fraction)->CusumResult:
    if not errors or any(e not in (0,1) for e in errors): raise Refusal("REFUSED[INVALID_CUSUM_SERIES]")
    if not 0<=target<=1 or slack<0 or threshold<=0: raise Refusal("REFUSED[INVALID_CUSUM_PARAMETER]")
    pos=Fraction(0); neg=Fraction(0)
    for error in errors:
        centered=Fraction(error)-target; pos=max(Fraction(0),pos+centered-slack); neg=max(Fraction(0),neg-centered-slack)
        if pos>=threshold or neg>=threshold: return CusumResult(pos,neg,True)
    return CusumResult(pos,neg,False)
