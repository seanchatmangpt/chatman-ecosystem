from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Calibration:
    support:int; false_current:Fraction; false_stale:Fraction; pseudo_quorum:Fraction; state:str
def calibrate(rows,min_support=5,max_false_current=Fraction(1,10),max_pseudo=Fraction(1,10)):
    rows=tuple(rows); n=len(rows)
    if not n: return Calibration(0,Fraction(0),Fraction(0),Fraction(0),"INSUFFICIENT")
    fc=Fraction(sum(r.error=="FALSE_CURRENT" for r in rows),n); fs=Fraction(sum(r.error=="FALSE_STALE" for r in rows),n); pq=Fraction(sum(r.error=="PSEUDO_QUORUM" for r in rows),n)
    state="INSUFFICIENT" if n<min_support else "CALIBRATED" if fc<=max_false_current and pq<=max_pseudo else "UNRELIABLE"
    return Calibration(n,fc,fs,pq,state)
