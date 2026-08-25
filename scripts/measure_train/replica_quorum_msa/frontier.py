from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True,order=True)
class CalibrationModel:
    generation:int; model_digest:str; state:str
    def __post_init__(self):
        if self.generation<0 or len(self.model_digest)!=64: raise Refused("REFUSED[INVALID_CALIBRATION_MODEL]")
        if self.state not in {"INSUFFICIENT","CALIBRATED","UNRELIABLE"}: raise Refused("REFUSED[INVALID_CALIBRATION_STATE]")
def current_frontier(models):
    models=tuple(models)
    if not models:return None
    g=max(m.generation for m in models); current=[m for m in models if m.generation==g]
    if len(set(m.model_digest for m in current))!=1: raise Refused("REFUSED[DIVERGENT_CALIBRATION_FRONTIER]")
    return current[0]
def admit_current(model,frontier):
    if frontier is None or model!=frontier: raise Refused("REFUSED[STALE_CALIBRATION_MODEL]")
    if model.state!="CALIBRATED": raise Refused("REFUSED[UNCALIBRATED_QUORUM_SENSOR]")
    return True
