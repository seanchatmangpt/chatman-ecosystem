from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class CalibrationModel:
    estimator: str
    generation: int
    digest: str
    state: str
    def __post_init__(self):
        if self.generation < 0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_CALIBRATION_MODEL]")
def current_frontier(models):
    by={}
    for m in models:
        old=by.get(m.estimator)
        if old is None or m.generation>old.generation: by[m.estimator]=m
        elif m.generation==old.generation and m.digest!=old.digest:
            raise Refused("REFUSED[DIVERGENT_BOUND_FRONTIER]")
    return tuple(sorted(by.values()))
