from dataclasses import dataclass
from .calibration import BoundCalibration
from .refusal import Refused

@dataclass(frozen=True)
class CalibrationFrontier:
    entries: tuple[BoundCalibration, ...]
    def current(self) -> BoundCalibration:
        if not self.entries: raise Refused("EMPTY_CALIBRATION_FRONTIER")
        generation = max(e.generation for e in self.entries)
        latest = tuple(e for e in self.entries if e.generation == generation)
        digests = {e.digest for e in latest}
        if len(digests) != 1: raise Refused("DIVERGENT_CALIBRATION_FRONTIER")
        return latest[0]
    def require(self, generation: int, digest: str):
        cur = self.current()
        if cur.generation != generation or cur.digest != digest:
            raise Refused("STALE_CALIBRATION")
        return cur
