from dataclasses import dataclass
from fractions import Fraction
from .error import error_profile

@dataclass(frozen=True)
class Calibration:
    estimator_id: str
    support: int
    bias: Fraction
    mae: Fraction
    mse: Fraction
    state: str

def calibrate(estimator_id,cases,min_support=3,max_mae=Fraction(1,4)):
    p=error_profile(cases)
    if p.n < min_support: state="INSUFFICIENT"
    elif p.mae > max_mae: state="UNRELIABLE"
    else: state="CALIBRATED"
    return Calibration(estimator_id,p.n,p.bias,p.mae,p.mse,state)
