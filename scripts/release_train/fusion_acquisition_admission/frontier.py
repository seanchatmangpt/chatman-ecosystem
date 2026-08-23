from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class CalibrationFrontier:
    generation: int
    digests: tuple[str, ...]

def frontier(calibrations):
    if not calibrations:
        raise Refused("EMPTY_CALIBRATION_FRONTIER")
    generation=max(c.sensor.generation for c in calibrations)
    current=[c for c in calibrations if c.sensor.generation == generation]
    by_sensor={}
    for c in current:
        prior=by_sensor.get(c.sensor.sensor_id)
        if prior and prior.sensor.calibration_digest != c.sensor.calibration_digest:
            raise Refused("DIVERGENT_CURRENT_CALIBRATION")
        by_sensor[c.sensor.sensor_id]=c
    return CalibrationFrontier(generation, tuple(sorted(c.sensor.calibration_digest for c in by_sensor.values())))

def require_current(calibration, current):
    if calibration.sensor.generation != current.generation:
        raise Refused("STALE_CALIBRATION_GENERATION")
    if calibration.sensor.calibration_digest not in current.digests:
        raise Refused("CALIBRATION_DIGEST_NOT_CURRENT")
