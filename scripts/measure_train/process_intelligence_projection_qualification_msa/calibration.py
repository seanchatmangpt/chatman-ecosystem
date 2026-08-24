from dataclasses import dataclass
from .confusion import classify
from .wilson import wilson_upper
@dataclass(frozen=True)
class Calibration:
    support:int; false_equivalent_upper:float; state:str
def calibrate(observations,min_support=5,max_false_equiv=0.2):
    c=classify(observations); upper=wilson_upper(c.false_equivalent,c.support)
    state="INSUFFICIENT" if c.support<min_support else ("CALIBRATED" if upper<=max_false_equiv else "UNRELIABLE")
    return Calibration(c.support,upper,state)
