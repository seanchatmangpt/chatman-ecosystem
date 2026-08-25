from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class CurrentnessBounds:
    lower: Fraction
    upper: Fraction
    width: Fraction

def identify(census):
    req=[r for r in census if r[1]]
    n=len(req)
    if n==0:
        return CurrentnessBounds(Fraction(1),Fraction(1),Fraction(0))
    exact=sum(1 for r in req if r[2]=="EXACT")
    potentially_exact=sum(1 for r in req if r[2] in {"EXACT","CENSORED","UNKNOWN"})
    lower=Fraction(exact,n)
    upper=Fraction(potentially_exact,n)
    return CurrentnessBounds(lower,upper,upper-lower)
