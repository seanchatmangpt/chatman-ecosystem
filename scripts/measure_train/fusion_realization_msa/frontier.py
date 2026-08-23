from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class CalibrationFrontier:
    policy_id: str
    generation: int
    digest: str
    def __post_init__(self):
        if not self.policy_id.strip() or self.generation<0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_CALIBRATION_FRONTIER]")
def current_frontier(frontiers):
    rows=tuple(frontiers)
    if not rows: raise Refused("REFUSED[EMPTY_CALIBRATION_FRONTIER]")
    latest=max(x.generation for x in rows); current={x for x in rows if x.generation==latest}
    if len(current)!=1: raise Refused("REFUSED[DIVERGENT_CALIBRATION_FRONTIER]")
    return next(iter(current))
