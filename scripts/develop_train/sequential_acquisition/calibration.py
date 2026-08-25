from dataclasses import dataclass
from fractions import Fraction
from .probability import unit
from .refusals import Refused

@dataclass(frozen=True)
class GainCalibration:
    sensor_id: str
    generation: int
    support: int
    mean_error_bits: float
    max_abs_error_bits: float
    reliability: Fraction

    def __post_init__(self):
        if not self.sensor_id or self.generation < 0 or self.support < 0:
            raise Refused("REFUSED_INVALID_GAIN_CALIBRATION")
        object.__setattr__(self, "reliability", unit(self.reliability, "reliability"))

def admitted(calibration: GainCalibration, *, min_support=3, max_abs_error=0.5, min_reliability=Fraction(3, 4)) -> bool:
    return calibration.support >= min_support and calibration.max_abs_error_bits <= max_abs_error and calibration.reliability >= min_reliability
