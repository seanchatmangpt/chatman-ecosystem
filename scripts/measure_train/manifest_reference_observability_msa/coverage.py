from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Coverage:
    required: int
    exact: int
    advanced: int
    diverged: int
    censored: int
    unknown: int
    exact_fraction: Fraction
    observable_fraction: Fraction

def measure(census):
    req=[r for r in census if r[1]]
    n=len(req)
    counts={k:sum(1 for r in req if r[2]==k) for k in ("EXACT","ADVANCED","DIVERGED","CENSORED","UNKNOWN")}
    if n==0:
        return Coverage(0,0,0,0,0,0,Fraction(1),Fraction(1))
    observable=counts["EXACT"]+counts["ADVANCED"]+counts["DIVERGED"]
    return Coverage(n,counts["EXACT"],counts["ADVANCED"],counts["DIVERGED"],counts["CENSORED"],counts["UNKNOWN"],
                    Fraction(counts["EXACT"],n),Fraction(observable,n))
