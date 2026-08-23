from dataclasses import dataclass
from fractions import Fraction
from .intervals import Interval
from .refusal import Refused

@dataclass(frozen=True)
class BoundCalibration:
    support: int
    coverage: Fraction
    mean_width: Fraction
    generation: int
    digest: str
    def admitted(self, min_support: int, min_coverage: Fraction, max_width: Fraction):
        if self.support < min_support: raise Refused("CALIBRATION_UNDER_SUPPORTED")
        if self.coverage < min_coverage: raise Refused("CALIBRATION_UNDER_COVERAGE")
        if self.mean_width > max_width: raise Refused("CALIBRATION_UNINFORMATIVE")
        if self.generation < 0 or len(self.digest) != 64: raise Refused("INVALID_CALIBRATION_IDENTITY")
        return self

def calibrated_interval(interval: Interval, calibration: BoundCalibration) -> Interval:
    miss = max(Fraction(0), Fraction(1) - calibration.coverage)
    penalty = interval.width * miss
    return interval.expand(penalty)
