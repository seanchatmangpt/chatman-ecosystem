from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class Calibration:
    generation: int
    digest: str
    support: int
    mean_error: Fraction
    max_error: Fraction
    def admitted(self, min_support=8, max_error=Fraction(1,5)):
        return self.support>=min_support and self.mean_error<=max_error and self.max_error<=max_error

def current(models):
    if not models: raise Refused("MISSING_CALIBRATION")
    g=max(m.generation for m in models); latest=[m for m in models if m.generation==g]
    if len({m.digest for m in latest}) != 1: raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    model=latest[0]
    if not model.admitted(): raise Refused("UNCALIBRATED_CURRENT_MODEL")
    return model
