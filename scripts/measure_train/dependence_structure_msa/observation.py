from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class PairObservation:
    subject: Subject
    left_id: str
    right_id: str
    observation_id: str
    left: bool
    right: bool
    stratum: str
    observed_at: datetime

    def __post_init__(self):
        if not self.left_id or not self.right_id or self.left_id == self.right_id:
            raise Refused("REFUSED[INVALID_EVIDENCE_PAIR]")
        if not self.observation_id or not self.stratum:
            raise Refused("REFUSED[INVALID_OBSERVATION_IDENTITY]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_OBSERVATION_TIME]")
