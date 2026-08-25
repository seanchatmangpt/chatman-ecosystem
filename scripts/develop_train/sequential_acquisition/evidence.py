from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from .probability import unit
from .refusals import Refused

@dataclass(frozen=True)
class ObservationEvidence:
    sensor_id: str
    observation_id: str
    observed_at: datetime
    likelihoods: dict[str, Fraction]
    realized_cost: Fraction
    realized_latency: Fraction

    def __post_init__(self):
        if not self.sensor_id or not self.observation_id:
            raise Refused("REFUSED_INVALID_EVIDENCE_IDENTITY")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED_NAIVE_EVIDENCE_TIME")
        if self.observed_at > datetime.now(timezone.utc):
            raise Refused("REFUSED_FUTURE_EVIDENCE")
        if not self.likelihoods:
            raise Refused("REFUSED_EMPTY_LIKELIHOODS")
        object.__setattr__(self, "likelihoods", {k: unit(v, "likelihood") for k, v in self.likelihoods.items()})
        if self.realized_cost < 0 or self.realized_latency < 0:
            raise Refused("REFUSED_NEGATIVE_REALIZATION")
