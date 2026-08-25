from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class Case:
    predicted_lo:float; predicted_hi:float; truth:float
    def __post_init__(self):
        if not (0<=self.predicted_lo<=self.predicted_hi<=1 and 0<=self.truth<=1): raise Refused("INVALID_CALIBRATION_CASE")
@dataclass(frozen=True)
class Calibration:
    mode:str; generation:int; digest:str; support:int; coverage:float; miss_rate:float; mean_width:float
def calibrate(mode,generation,digest,cases):
    if generation<0 or len(digest)!=64: raise Refused("INVALID_CALIBRATION_ID")
    cases=list(cases)
    if not cases: raise Refused("INSUFFICIENT_CALIBRATION_SUPPORT")
    hits=sum(c.predicted_lo<=c.truth<=c.predicted_hi for c in cases)
    widths=[c.predicted_hi-c.predicted_lo for c in cases]
    return Calibration(mode,generation,digest,len(cases),hits/len(cases),1-hits/len(cases),sum(widths)/len(widths))
