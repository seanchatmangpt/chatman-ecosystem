from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .calibration import CalibrationModel
from .subject import Refusal
_STATES={"STABLE","DRIFT","INSUFFICIENT"}
@dataclass(frozen=True,slots=True)
class CalibrationRegime:
    source_id:str; generation:int; state:str; model:CalibrationModel|None; observed_at:datetime
    def __post_init__(self)->None:
        if self.generation<0: raise Refusal("REFUSED[INVALID_REGIME_GENERATION]")
        if self.state not in _STATES: raise Refusal("REFUSED[INVALID_REGIME_STATE]")
        if self.observed_at.tzinfo is None: raise Refusal("REFUSED[NAIVE_REGIME_TIME]")
        if self.model is not None and self.model.source_id!=self.source_id: raise Refusal("REFUSED[REGIME_MODEL_SOURCE_MISMATCH]")
        if self.state=="INSUFFICIENT" and self.model is not None: raise Refusal("REFUSED[INSUFFICIENT_REGIME_HAS_MODEL]")
def advance_regime(previous:CalibrationRegime|None,*,state:str,model:CalibrationModel|None,observed_at:datetime)->CalibrationRegime:
    source_id=model.source_id if model else (previous.source_id if previous else "")
    if not source_id: raise Refusal("REFUSED[MISSING_REGIME_SOURCE]")
    return CalibrationRegime(source_id,0 if previous is None else previous.generation+1,state,model,observed_at)
