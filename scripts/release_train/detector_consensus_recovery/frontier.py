from dataclasses import dataclass
from .calibration import DetectorCalibration

@dataclass(frozen=True)
class CalibrationGeneration:
    detector_fingerprint: str
    generation: int
    calibration: DetectorCalibration
    current: bool=True
    def __post_init__(self):
        if self.generation < 1 or self.calibration.detector_fingerprint != self.detector_fingerprint:
            raise ValueError("REFUSED[INVALID_CALIBRATION_GENERATION]")

def unique_current(generations):
    currents=[g for g in generations if g.current]
    by={g.detector_fingerprint for g in currents}
    if len(currents)!=len(by): raise ValueError("REFUSED[DIVERGENT_CALIBRATION_FRONTIER]")
    return {g.detector_fingerprint:g for g in currents}
