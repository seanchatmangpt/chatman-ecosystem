import hashlib
import json
from dataclasses import dataclass

from .calibration import SensorCalibration

@dataclass(frozen=True)
class CalibrationFrontier:
    digest: str
    generations: tuple[tuple[str, int], ...]

    @classmethod
    def build(cls, calibrations: tuple[SensorCalibration, ...]) -> "CalibrationFrontier":
        generations = tuple(sorted((item.candidate_id, item.generation) for item in calibrations))
        if len({candidate_id for candidate_id, _ in generations}) != len(generations):
            raise ValueError("REFUSED[DUPLICATE_CALIBRATION_CANDIDATE]")
        payload = json.dumps(generations, separators=(",", ":"), sort_keys=True).encode()
        return cls(hashlib.sha256(payload).hexdigest(), generations)

    def assert_current(self, calibrations: tuple[SensorCalibration, ...]) -> None:
        current = self.build(calibrations)
        if current != self:
            raise ValueError("REFUSED[STALE_CALIBRATION_FRONTIER]")
