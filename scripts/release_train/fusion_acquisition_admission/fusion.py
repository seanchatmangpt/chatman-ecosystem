from dataclasses import dataclass
from statistics import median
from .errors import Refused
from .observation import Observation
from .sensor import Calibration

@dataclass(frozen=True)
class FusedEvidence:
    score: float
    verdict: str
    independent_sensor_ids: tuple[str, ...]
    max_leave_one_out_influence: float

def _signed(observation: Observation, calibration: Calibration):
    reliability=max(0.0, 1.0 - float(calibration.error_mass))
    sign={"CURRENT":1.0,"STALE":-1.0,"AMBIGUOUS":0.0}[observation.verdict]
    return sign * float(observation.confidence) * reliability

def robust_fuse(observations, calibrations, independent_ids):
    by_id={c.sensor.sensor_id:c for c in calibrations}
    chosen=[o for o in observations if o.sensor.sensor_id in set(independent_ids)]
    if len(chosen) < 2:
        raise Refused("INSUFFICIENT_INDEPENDENT_SENSORS")
    values=[_signed(o, by_id[o.sensor.sensor_id]) for o in chosen]
    center=float(median(values))
    influences=[]
    for i in range(len(values)):
        remaining=values[:i]+values[i+1:]
        influences.append(abs(center-float(median(remaining))))
    verdict="CURRENT" if center > 0.25 else "STALE" if center < -0.25 else "AMBIGUOUS"
    return FusedEvidence(center, verdict, tuple(sorted(independent_ids)), max(influences, default=0.0))
