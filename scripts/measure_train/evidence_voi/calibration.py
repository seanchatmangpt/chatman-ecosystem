from dataclasses import dataclass
from fractions import Fraction
from datetime import datetime
from .candidate import MeasurementCandidate
from .subject import Refused

@dataclass(frozen=True, order=True)
class SensorCalibration:
    candidate_id: str
    generation: int
    support: int
    sensitivity: Fraction
    false_positive_rate: Fraction
    observed_at: datetime
    def __post_init__(self):
        if not self.candidate_id.strip() or self.generation < 0 or self.support < 0:
            raise Refused("REFUSED[INVALID_CALIBRATION]")
        for value in (self.sensitivity, self.false_positive_rate):
            if not isinstance(value, Fraction) or value < 0 or value > 1:
                raise Refused("REFUSED[INVALID_CALIBRATION_RATE]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_CALIBRATION_TIME]")

def admit_calibration(candidate: MeasurementCandidate, calibration: SensorCalibration, now: datetime, min_support=8, max_age_seconds=3600):
    if calibration.candidate_id != candidate.candidate_id:
        raise Refused("REFUSED[FOREIGN_CALIBRATION]")
    if now.tzinfo is None or now.utcoffset() is None:
        raise Refused("REFUSED[NAIVE_NOW]")
    age=(now-calibration.observed_at).total_seconds()
    if age < 0:
        raise Refused("REFUSED[FUTURE_CALIBRATION]")
    if age > max_age_seconds:
        raise Refused("REFUSED[STALE_CALIBRATION]")
    if calibration.support < min_support:
        raise Refused("REFUSED[INSUFFICIENT_CALIBRATION_SUPPORT]")
    return calibration
