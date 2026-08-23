from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True, order=True)
class CalibrationModel:
    estimator_id: str
    generation: int
    digest: str
    calibration: object
    def __post_init__(self):
        if self.generation < 0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_CALIBRATION_MODEL]")

def current_frontier(models):
    latest={}
    for m in models:
        old=latest.get(m.estimator_id)
        if old is None or m.generation>old.generation: latest[m.estimator_id]=m
        elif m.generation==old.generation and m.digest!=old.digest: raise Refused("REFUSED[DIVERGENT_CALIBRATION_FRONTIER]")
    return tuple(sorted(latest.values()))
