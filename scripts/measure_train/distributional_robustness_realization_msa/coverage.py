from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Coverage:
    support:int; covered:int; misses:int; rate:Fraction; miss_rate:Fraction
def empirical_coverage(observations, member):
    rows=tuple(observations); n=len(rows)
    if n==0: return Coverage(0,0,0,Fraction(0),Fraction(0))
    covered=sum(1 for row in rows if member(row))
    return Coverage(n,covered,n-covered,Fraction(covered,n),Fraction(n-covered,n))
