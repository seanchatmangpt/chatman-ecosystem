from dataclasses import dataclass
from .calibration import BoundCalibration
from .refusal import Refused
@dataclass(frozen=True)
class CalibrationFrontier:
    calibrations:tuple[BoundCalibration,...]
    def current(self)->BoundCalibration:
        if not self.calibrations: raise Refused('EMPTY_CALIBRATION_FRONTIER')
        g=max(c.generation for c in self.calibrations)
        cur=[c for c in self.calibrations if c.generation==g]
        if len({c.digest for c in cur})!=1: raise Refused('DIVERGENT_CALIBRATION_FRONTIER')
        return sorted(cur,key=lambda c:c.digest)[0]
    def require(self,generation:int,digest:str)->BoundCalibration:
        c=self.current()
        if (c.generation,c.digest)!=(generation,digest): raise Refused('STALE_CALIBRATION')
        return c
