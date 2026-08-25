from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class BoundCalibration:
    support: int
    coverage: Fraction
    mean_width: Fraction
    miss_rate: Fraction
    state: str
def calibrate(cases, min_support=3, max_miss=Fraction(1,5)):
    rows=tuple(cases); n=len(rows)
    if n==0: return BoundCalibration(0,Fraction(0),Fraction(0),Fraction(0),"INSUFFICIENT")
    covered=sum(1 for c in rows if c.covers)
    coverage=Fraction(covered,n); miss=1-coverage
    width=sum((c.bound.width for c in rows),Fraction(0))/n
    state="INSUFFICIENT" if n<min_support else ("CALIBRATED" if miss<=max_miss else "UNRELIABLE")
    return BoundCalibration(n,coverage,width,miss,state)
