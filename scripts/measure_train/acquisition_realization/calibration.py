from dataclasses import dataclass
from statistics import mean
from .subject import Refused

@dataclass(frozen=True)
class GainCalibration:
    support: int
    mean_error: float
    mean_absolute_error: float
    calibration_state: str


def calibrate(realizations, min_support=5, max_mae=0.25):
    rows=tuple(realizations)
    if min_support <= 0 or max_mae < 0:
        raise Refused("REFUSED[INVALID_CALIBRATION_POLICY]")
    if not rows:
        return GainCalibration(0,0.0,0.0,"INSUFFICIENT")
    errors=[r.gain_error for r in rows]
    mae=mean(abs(e) for e in errors)
    state="INSUFFICIENT" if len(rows)<min_support else "CALIBRATED" if mae<=max_mae else "UNRELIABLE"
    return GainCalibration(len(rows),mean(errors),mae,state)
