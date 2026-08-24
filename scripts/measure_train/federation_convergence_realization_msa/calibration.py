from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Calibration:
    support:int; false_fixed:Fraction; false_nonfixed:Fraction; state:str
def calibrate(rows,min_support=5,max_false_fixed=Fraction(1,5)):
    n=len(rows)
    if not n: return Calibration(0,Fraction(0),Fraction(0),'INSUFFICIENT')
    ff=sum(r.predicted_fixed and r.state!='FIXED' for r in rows); fn=sum((not r.predicted_fixed) and r.state=='FIXED' for r in rows)
    state='INSUFFICIENT' if n<min_support else ('CALIBRATED' if Fraction(ff,n)<=max_false_fixed else 'UNRELIABLE')
    return Calibration(n,Fraction(ff,n),Fraction(fn,n),state)
