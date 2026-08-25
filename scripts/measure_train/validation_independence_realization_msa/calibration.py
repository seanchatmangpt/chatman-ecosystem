from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Calibration:
    support:int; false_independent:Fraction; false_dependent:Fraction; accuracy:Fraction; state:str
def calibrate(trials,min_support=6,max_false_independent=Fraction(1,10)):
    rows=tuple(trials); n=len(rows)
    if not n:return Calibration(0,Fraction(0),Fraction(0),Fraction(0),"INSUFFICIENT")
    fi=sum(t.predicted=="INDEPENDENT" and t.truth=="DEPENDENT" for t in rows); fd=sum(t.predicted=="DEPENDENT" and t.truth=="INDEPENDENT" for t in rows)
    acc=Fraction(sum(t.predicted==t.truth for t in rows),n)
    state="INSUFFICIENT" if n<min_support else ("CALIBRATED" if Fraction(fi,n)<=max_false_independent else "UNRELIABLE")
    return Calibration(n,Fraction(fi,n),Fraction(fd,n),acc,state)
