from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
from .epoch import EpochStamp

OUTCOMES={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}

@dataclass(frozen=True, order=True)
class Observation:
    consumer: Subject
    producer_epoch: EpochStamp
    scope: str
    outcome: str
    evidence_id: str
    observed_at: datetime

    def __post_init__(self):
        if self.scope not in {"FOCUSED","REPOSITORY","RUNTIME","ARTIFACT","DEPENDENCY","RECEIPT"}:
            raise Refused("REFUSED[INVALID_SCOPE]")
        if self.outcome not in OUTCOMES:
            raise Refused("REFUSED[INVALID_OUTCOME]")
        if not self.evidence_id.strip():
            raise Refused("REFUSED[EMPTY_EVIDENCE_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_OBSERVATION_TIME]")
