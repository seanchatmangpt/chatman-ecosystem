from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class ErrorProfile:
    n: int
    bias: Fraction
    mae: Fraction
    mse: Fraction
    max_abs_error: Fraction

def error_profile(cases):
    if not cases: return ErrorProfile(0,Fraction(0),Fraction(0),Fraction(0),Fraction(0))
    es=[c.estimate-c.truth for c in cases]
    n=len(es)
    return ErrorProfile(n,sum(es,Fraction(0))/n,sum((abs(e) for e in es),Fraction(0))/n,sum((e*e for e in es),Fraction(0))/n,max(abs(e) for e in es))
