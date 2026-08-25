from dataclasses import dataclass
from fractions import Fraction
from .interval import Interval
from .refusal import Refused
@dataclass(frozen=True)
class BoundCalibration:
    generation:int
    digest:str
    support:int
    coverage:Fraction
    mean_width:Fraction
    max_width:Fraction
    def __post_init__(self):
        if self.generation<0 or self.support<0: raise Refused('INVALID_CALIBRATION')
        if not (0<=self.coverage<=1): raise Refused('INVALID_COVERAGE')
        if self.mean_width<0 or self.max_width<self.mean_width: raise Refused('INVALID_WIDTH')
    def admitted(self,min_support:int,min_coverage:Fraction,max_mean_width:Fraction)->bool:
        return self.support>=min_support and self.coverage>=min_coverage and self.mean_width<=max_mean_width

def calibrated_interval(raw:Interval, calibration:BoundCalibration, penalty:Fraction)->Interval:
    if penalty<0: raise Refused('NEGATIVE_CALIBRATION_PENALTY')
    miss=1-calibration.coverage
    widen=penalty*miss
    return Interval(raw.lower-widen,raw.upper+widen)
