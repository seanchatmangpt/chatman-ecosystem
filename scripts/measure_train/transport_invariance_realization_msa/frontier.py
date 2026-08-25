from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True,order=True)
class StressCalibrationModel:
    generation:int
    digest:str
    support:int
    max_false_stable_rate:float
    max_mae:float
    state:str
    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_STRESS_CALIBRATION_MODEL]")
        if self.support<0: raise Refused("REFUSED[INVALID_CALIBRATION_SUPPORT]")
def current(models):
    rows=tuple(models)
    if not rows: raise Refused("REFUSED[MISSING_STRESS_CALIBRATION]")
    generation=max(m.generation for m in rows); latest=[m for m in rows if m.generation==generation]
    if len({m.digest for m in latest})!=1: raise Refused("REFUSED[DIVERGENT_CURRENT_STRESS_CALIBRATION]")
    return latest[0]
