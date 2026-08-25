from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .refusal import Refused

STATES = {"ACTIVE", "FIXED", "REGRESSED", "BLOCKED"}

@dataclass(frozen=True, order=True)
class Observation:
    subject: Subject
    episode_id: str
    step: int
    state: str
    predicted_on_time: Fraction
    common_cause: str
    methodology: str
    engine: str
    region: str
    evidence_root: str
    observed_at: datetime

    def __post_init__(self):
        if not self.episode_id or self.step < 0:
            raise Refused("INVALID_OBSERVATION_IDENTITY")
        if self.state not in STATES:
            raise Refused("INVALID_CONVERGENCE_STATE")
        if not (0 <= self.predicted_on_time <= 1):
            raise Refused("INVALID_PREDICTION")
        if not all((self.common_cause, self.methodology, self.engine, self.region, self.evidence_root)):
            raise Refused("INCOMPLETE_PROVENANCE")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("NAIVE_OBSERVATION_TIME")
