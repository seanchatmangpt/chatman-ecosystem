from dataclasses import dataclass
from .sensor import Sensor
from .refusals import Refused

@dataclass(frozen=True)
class CalibrationFrontier:
    generation: int
    digests: tuple[str,...]

def frontier(sensors: list[Sensor]) -> CalibrationFrontier:
    if not sensors: raise Refused("EMPTY_SENSOR_SET")
    generation=max(s.calibration.generation for s in sensors)
    current=[s for s in sensors if s.calibration.generation==generation]
    by_id={s.sensor_id:s.calibration.digest for s in current}
    if len(by_id)!=len(current): raise Refused("DUPLICATE_SENSOR")
    return CalibrationFrontier(generation, tuple(sorted(by_id.values())))

def require_current(sensors: list[Sensor], expected: CalibrationFrontier) -> None:
    actual=frontier(sensors)
    if actual != expected: raise Refused("STALE_CALIBRATION_FRONTIER")
