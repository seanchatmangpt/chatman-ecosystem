from dataclasses import dataclass
from fractions import Fraction
from math import sqrt
from .refusal import Refused

@dataclass(frozen=True)
class RealizationCalibration:
    generation:int; support:int; mean_abs_error:Fraction; regret:Fraction; upper_error:Fraction
    def admit(self, min_support=5, max_error=Fraction(1,4), max_regret=Fraction(1,4)):
        if self.support<min_support: raise Refused("INSUFFICIENT_REALIZATION_SUPPORT")
        if self.upper_error>max_error: raise Refused("UNRELIABLE_REALIZATION_CALIBRATION")
        if self.regret>max_regret: raise Refused("EXCESSIVE_REALIZED_REGRET")
        return True

def wilson_upper(failures:int,total:int,z=1.96):
    if total<=0 or not 0<=failures<=total: raise Refused("INVALID_CALIBRATION_COUNTS")
    p=failures/total; d=1+z*z/total; c=(p+z*z/(2*total))/d
    r=z*sqrt((p*(1-p)+z*z/(4*total))/total)/d
    return Fraction(str(min(1.0,c+r))).limit_denominator(1_000_000)
