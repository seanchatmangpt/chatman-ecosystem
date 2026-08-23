import math
from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class LossMatrix:
    false_stable: Fraction
    false_unstable: Fraction
    def __post_init__(self):
        if self.false_stable<0 or self.false_unstable<0: raise Refused("REFUSED[NEGATIVE_LOSS]")
        if self.false_stable==self.false_unstable==0: raise Refused("REFUSED[VACUOUS_LOSS]")
@dataclass(frozen=True)
class RiskCalibration:
    support:int
    mae:Fraction
    bias:Fraction
    state:str
def realized_loss(cases,loss):
    rows=tuple(cases)
    if not rows:return Fraction(0)
    total=Fraction(0)
    for c in rows:
        if c.predicted_invariant and not c.observed_success: total+=loss.false_stable
        elif not c.predicted_invariant and c.observed_success: total+=loss.false_unstable
    return total/len(rows)
def wilson_upper(errors,total,z=1.96):
    if total<=0:return 1.0
    p=errors/total; z2=z*z
    center=(p+z2/(2*total))/(1+z2/total)
    radius=z*math.sqrt((p*(1-p)+z2/(4*total))/total)/(1+z2/total)
    return min(1.0,center+radius)
def hoeffding_radius(total,delta=0.05):
    if total<=0:return 1.0
    return math.sqrt(math.log(2/delta)/(2*total))
def calibrate_risk(cases,min_support=5,max_mae=Fraction(1,5),max_abs_bias=Fraction(1,5)):
    rows=tuple(cases)
    if not rows:return RiskCalibration(0,Fraction(0),Fraction(0),"INSUFFICIENT")
    errs=[c.predicted_risk-c.observed_risk for c in rows]
    mae=sum((abs(e) for e in errs),Fraction(0))/len(rows)
    bias=sum(errs,Fraction(0))/len(rows)
    state="INSUFFICIENT" if len(rows)<min_support else ("CALIBRATED" if mae<=max_mae and abs(bias)<=max_abs_bias else "UNRELIABLE")
    return RiskCalibration(len(rows),mae,bias,state)
