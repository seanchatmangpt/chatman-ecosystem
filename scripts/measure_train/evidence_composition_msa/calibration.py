from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class CompositionCalibration:
    support:int
    coverage:Fraction
    miss_rate:Fraction
    mean_width:Fraction
    state:str
def calibrate(cases,min_support=5,max_miss=Fraction(1,5)):
    rows=tuple(cases); n=len(rows)
    if not n: return CompositionCalibration(0,Fraction(0),Fraction(0),Fraction(0),"INSUFFICIENT")
    covered=sum(1 for c in rows if c.covered)
    coverage=Fraction(covered,n); miss=1-coverage
    width=sum((c.predicted.width for c in rows),Fraction(0))/n
    state="INSUFFICIENT" if n<min_support else ("CALIBRATED" if miss<=max_miss else "UNRELIABLE")
    return CompositionCalibration(n,coverage,miss,width,state)
