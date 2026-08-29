from dataclasses import dataclass
from .subject import Subject, Refused
from .schema import CalibrationSchema
from .interval import Interval
@dataclass(frozen=True, order=True)
class CalibrationEpoch:
    source:str; subject:Subject; generation:int; model_digest:str; schema:CalibrationSchema; window:Interval; support:int; state:str
    def __post_init__(self):
        if not self.source.strip(): raise Refused("REFUSED[EMPTY_SOURCE]")
        if self.generation<0: raise Refused("REFUSED[INVALID_GENERATION]")
        if len(self.model_digest)!=64 or any(c not in "0123456789abcdef" for c in self.model_digest): raise Refused("REFUSED[INVALID_MODEL_DIGEST]")
        if self.support<0: raise Refused("REFUSED[INVALID_SUPPORT]")
        if self.state not in {"STABLE","DRIFT","INSUFFICIENT"}: raise Refused("REFUSED[INVALID_REGIME_STATE]")
