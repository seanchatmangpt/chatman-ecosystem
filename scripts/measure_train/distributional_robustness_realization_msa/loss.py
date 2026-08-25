from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class LossCalibration:
    support:int; mae:Fraction; bias:Fraction; false_safe:int; false_conservative:int
def calibrate_loss(observations):
    rows=tuple(observations)
    if not rows: return LossCalibration(0,Fraction(0),Fraction(0),0,0)
    errors=[r.predicted_worst_loss-r.realized_loss for r in rows]
    return LossCalibration(len(rows),sum((abs(e) for e in errors),Fraction(0))/len(rows),sum(errors,Fraction(0))/len(rows),sum(1 for e in errors if e<0),sum(1 for e in errors if e>0))
