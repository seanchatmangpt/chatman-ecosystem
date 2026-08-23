from dataclasses import dataclass
from datetime import datetime
from .exact import nonnegative
from .errors import Refused
@dataclass(frozen=True)
class StepRealization:
    index: int
    evidence_id: str
    predicted_gain: object
    realized_gain: object
    cost: object
    latency: object
    samples: int
    observed_at: datetime
    outcome: str="PASS"
    def __post_init__(self):
        if self.index < 0 or not self.evidence_id or self.samples < 0:
            raise Refused("INVALID_REALIZATION")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("NAIVE_TIME")
        object.__setattr__(self,"predicted_gain",nonnegative(self.predicted_gain))
        object.__setattr__(self,"realized_gain",nonnegative(self.realized_gain))
        object.__setattr__(self,"cost",nonnegative(self.cost))
        object.__setattr__(self,"latency",nonnegative(self.latency))
        if self.outcome not in {"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}:
            raise Refused("INVALID_OUTCOME")
    @property
    def residual(self): return self.realized_gain-self.predicted_gain
