from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Calibration:
    support:int; max_gap:Fraction; oracle_mae:Fraction; realized_mae:Fraction; false_safe_rate:Fraction; state:str
def calibrate(f,d,r,min_support=3,max_mae=Fraction(1,20),max_false_safe=Fraction(0)):
    state="INSUFFICIENT" if f.support<min_support else ("CALIBRATED" if f.dual_feasible and f.complementary_slackness and f.zero_gap and d.mae<=max_mae and r.mae<=max_mae and r.false_safe_rate<=max_false_safe else "UNRELIABLE")
    return Calibration(f.support,f.max_gap,d.mae,r.mae,r.false_safe_rate,state)
