from dataclasses import dataclass
from datetime import datetime,timedelta
from fractions import Fraction
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class SensorCalibration:
    candidate_id:str; generation:int; support:int; true_positive_rate:Fraction; false_positive_rate:Fraction; observed_at:datetime
    def __post_init__(self):
        if self.generation<0 or self.support<0 or self.observed_at.tzinfo is None: raise Refusal('REFUSED_INVALID_CALIBRATION')
        if any(x<0 or x>1 for x in (self.true_positive_rate,self.false_positive_rate)): raise Refusal('REFUSED_INVALID_CALIBRATION')
    def admit(self,*,now,min_support=8,max_age=timedelta(hours=6)):
        if now.tzinfo is None: raise Refusal('REFUSED_NAIVE_TIME')
        if self.observed_at>now: raise Refusal('REFUSED_FUTURE_CALIBRATION')
        if self.support<min_support: raise Refusal('REFUSED_INSUFFICIENT_CALIBRATION')
        if now-self.observed_at>max_age: raise Refusal('REFUSED_STALE_CALIBRATION')
        if self.true_positive_rate<=self.false_positive_rate: raise Refusal('REFUSED_UNRELIABLE_CALIBRATION')
