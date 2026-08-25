from dataclasses import dataclass
from fractions import Fraction
from enum import StrEnum
from .errors import Refused
class CalibrationState(StrEnum): INSUFFICIENT='INSUFFICIENT'; CALIBRATED='CALIBRATED'; UNRELIABLE='UNRELIABLE'
@dataclass(frozen=True, slots=True)
class Calibration:
    generation:int; digest:str; support:int; mae:Fraction; max_mae:Fraction=Fraction(1,5)
    @property
    def state(self):
        if self.support < 3: return CalibrationState.INSUFFICIENT
        return CalibrationState.CALIBRATED if self.mae <= self.max_mae else CalibrationState.UNRELIABLE
def require_current(models):
    models=tuple(models)
    if not models: raise Refused('REFUSED_NO_CALIBRATION')
    g=max(m.generation for m in models); latest=[m for m in models if m.generation==g]
    if len({m.digest for m in latest}) != 1: raise Refused('REFUSED_DIVERGENT_CALIBRATION_FRONTIER')
    m=latest[0]
    if m.state is not CalibrationState.CALIBRATED: raise Refused('REFUSED_UNRELIABLE_CALIBRATION')
    return m
