from dataclasses import dataclass
from fractions import Fraction
from statistics import median

@dataclass(frozen=True)
class DetectorCalibration:
    detector_fingerprint: str
    support: int
    false_alarm_rate: Fraction
    miss_rate: Fraction
    median_delay: Fraction
    state: str

def calibrate(observations, min_support=6, max_far=Fraction(1,4), max_miss=Fraction(1,4), max_delay=Fraction(4,1)):
    obs=list(observations)
    if not obs: raise ValueError("REFUSED[EMPTY_CALIBRATION]")
    fps={o.detector.fingerprint for o in obs}
    if len(fps)!=1: raise ValueError("REFUSED[MIXED_DETECTORS]")
    ids=[o.case_id for o in obs]
    if len(ids)!=len(set(ids)): raise ValueError("REFUSED[DUPLICATE_CALIBRATION_CASE]")
    negatives=[o for o in obs if not o.expected_drift]; positives=[o for o in obs if o.expected_drift]
    far=Fraction(sum(o.detected_drift for o in negatives), len(negatives) or 1)
    miss=Fraction(sum(not o.detected_drift for o in positives), len(positives) or 1)
    delays=[o.delay_steps for o in positives if o.detected_drift and o.delay_steps is not None]
    delay=Fraction(int(median(delays)) if delays else 10**6,1)
    state="INSUFFICIENT" if len(obs)<min_support else ("UNRELIABLE" if far>max_far or miss>max_miss or delay>max_delay else "CALIBRATED")
    return DetectorCalibration(next(iter(fps)),len(obs),far,miss,delay,state)
