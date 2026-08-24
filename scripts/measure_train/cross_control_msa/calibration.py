from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Calibration: support:int; false_consistent:Fraction; false_inconsistent:Fraction; state:str
def calibrate(predicted,truth,min_support=5,max_error=Fraction(1,5)):
 rows=list(zip(predicted,truth)); n=len(rows)
 if not n:return Calibration(0,Fraction(0),Fraction(0),"INSUFFICIENT")
 fc=sum(p and not t for p,t in rows); fi=sum((not p) and t for p,t in rows)
 state="INSUFFICIENT" if n<min_support else ("CALIBRATED" if Fraction(max(fc,fi),n)<=max_error else "UNRELIABLE")
 return Calibration(n,Fraction(fc,n),Fraction(fi,n),state)
