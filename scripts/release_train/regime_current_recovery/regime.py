from dataclasses import dataclass
from enum import Enum
from .calibration import CalibrationModel
from .subject import Refusal

class RegimeState(str, Enum):
    STABLE='STABLE'; DRIFT='DRIFT'; INSUFFICIENT='INSUFFICIENT'

@dataclass(frozen=True)
class CalibrationRegime:
    model: CalibrationModel
    generation: int
    state: RegimeState
    detector: str
    def __post_init__(self) -> None:
        if self.generation < 0: raise Refusal('REFUSED[INVALID_REGIME_GENERATION]')
        if not self.detector: raise Refusal('REFUSED[EMPTY_REGIME_DETECTOR]')

def advance(previous: CalibrationRegime|None, model: CalibrationModel, state: RegimeState, detector: str) -> CalibrationRegime:
    if previous is not None and (previous.model.subject != model.subject or previous.model.source_id != model.source_id):
        raise Refusal('REFUSED[FOREIGN_REGIME_TRANSITION]')
    generation=0 if previous is None else previous.generation + (state != previous.state or model != previous.model)
    return CalibrationRegime(model,generation,state,detector)
