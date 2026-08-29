from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Trajectory:
    steps: tuple
    def __post_init__(self):
        if not self.steps: raise Refused("EMPTY_TRAJECTORY")
        ids=set(); prior_time=None
        for expected,s in enumerate(self.steps):
            if s.index != expected: raise Refused("NONCONTIGUOUS_TRAJECTORY")
            if s.evidence_id in ids: raise Refused("DUPLICATE_EVIDENCE")
            if prior_time is not None and s.observed_at <= prior_time: raise Refused("TIME_REGRESSION")
            ids.add(s.evidence_id); prior_time=s.observed_at
    @property
    def residuals(self): return tuple(s.residual for s in self.steps)
    @property
    def total_predicted(self): return sum((s.predicted_gain for s in self.steps),0)
    @property
    def total_realized(self): return sum((s.realized_gain for s in self.steps),0)
