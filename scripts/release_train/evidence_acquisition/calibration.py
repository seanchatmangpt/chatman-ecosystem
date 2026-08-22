from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction

@dataclass(frozen=True)
class SensorCalibration:
    candidate_id: str
    generation: int
    support: int
    tpr: Fraction
    fpr: Fraction
    observed_at: datetime

    def __post_init__(self):
        if not self.candidate_id or self.generation < 0 or self.support < 0:
            raise ValueError("REFUSED[INVALID_CALIBRATION]")
        if not (Fraction(0) <= self.fpr <= Fraction(1) and Fraction(0) <= self.tpr <= Fraction(1)):
            raise ValueError("REFUSED[INVALID_CALIBRATION_RATE]")

    def admit(self, now: datetime, min_support: int = 8, max_age_seconds: int = 7200) -> None:
        if self.observed_at.tzinfo is None or now.tzinfo is None:
            raise ValueError("REFUSED[NAIVE_CALIBRATION_TIME]")
        observed = self.observed_at.astimezone(timezone.utc)
        current = now.astimezone(timezone.utc)
        age = (current - observed).total_seconds()
        if age < 0:
            raise ValueError("REFUSED[FUTURE_CALIBRATION]")
        if age > max_age_seconds:
            raise ValueError("REFUSED[STALE_CALIBRATION]")
        if self.support < min_support:
            raise ValueError("REFUSED[INSUFFICIENT_CALIBRATION_SUPPORT]")
        if self.tpr <= self.fpr:
            raise ValueError("REFUSED[UNINFORMATIVE_CALIBRATION]")
