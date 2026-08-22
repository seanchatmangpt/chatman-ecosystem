from dataclasses import dataclass
from fractions import Fraction
from .metrics import DetectorMetrics
from .subject import Refused

@dataclass(frozen=True)
class DetectorCalibration:
    policy_fingerprint: str
    generation: int
    support: int
    false_alarm_rate: Fraction
    miss_rate: Fraction
    median_delay_seconds: Fraction
    state: str

def calibrate(metrics: DetectorMetrics, generation: int, min_support=4,
              max_false_alarm=Fraction(1, 4), max_miss=Fraction(1, 4), max_delay_seconds=Fraction(60)):
    if generation < 0 or min_support < 1:
        raise Refused("REFUSED[INVALID_CALIBRATION_POLICY]")
    if metrics.support < min_support:
        state = "INSUFFICIENT"
    elif metrics.false_alarm_rate > max_false_alarm or metrics.miss_rate > max_miss or metrics.median_delay_seconds > max_delay_seconds:
        state = "UNRELIABLE"
    else:
        state = "CALIBRATED"
    return DetectorCalibration(metrics.policy_fingerprint, generation, metrics.support, metrics.false_alarm_rate,
                               metrics.miss_rate, metrics.median_delay_seconds, state)
