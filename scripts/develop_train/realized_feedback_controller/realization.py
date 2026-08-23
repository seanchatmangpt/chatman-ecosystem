from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .errors import Refused
from .rational import nonnegative

@dataclass(frozen=True)
class StepRealization:
    step: int
    evidence_id: str
    predicted_gain: Fraction
    realized_gain: Fraction
    cost: Fraction
    latency: Fraction
    samples: int
    observed_at: datetime

    def __post_init__(self):
        if self.step < 0 or not self.evidence_id or self.samples < 1:
            raise Refused("REFUSED_INVALID_REALIZATION")
        if self.observed_at.tzinfo is None:
            raise Refused("REFUSED_NAIVE_OBSERVATION_TIME")
        for value in (self.predicted_gain, self.realized_gain, self.cost, self.latency):
            nonnegative(value)

    @property
    def residual(self):
        return self.realized_gain - self.predicted_gain
