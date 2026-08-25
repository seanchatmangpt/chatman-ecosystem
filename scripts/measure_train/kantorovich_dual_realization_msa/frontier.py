from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True, order=True)
class CalibrationModel:
    generation:int; digest:str; state:str
    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_CALIBRATION_MODEL]")
def current(models):
    rows=sorted(models,key=lambda m:m.generation)
    if not rows:return None
    latest=rows[-1]
    if any(m.digest!=latest.digest for m in rows if m.generation==latest.generation): raise Refused("REFUSED[DIVERGENT_CURRENT_CERTIFICATE_MODEL]")
    return latest
