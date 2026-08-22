from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from .epoch import EpochStamp
from .subject import Subject

class Scope(str, Enum):
    FOCUSED='FOCUSED'; REPOSITORY='REPOSITORY'; RUNTIME='RUNTIME'; DEPENDENCY='DEPENDENDENCY'; RECEIPT='RECEIPT'
class Outcome(str, Enum):
    PASS='PASS'; FAIL='FAIL'; PENDING='PENDING'; UNKNOWN='UNKNOWN'; UNSUPPORTED='UNSUPPORTED'

@dataclass(frozen=True)
class Observation:
    consumer: Subject
    epoch: EpochStamp
    scope: Scope
    outcome: Outcome
    evidence_id: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError('REFUSED[MISSING_EVIDENCE_ID]')
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError('REFUSED[NAIVE_OBSERVATION_TIME]')
        if self.observed_at < self.epoch.observed_at:
            raise ValueError('REFUSED[PRE_EPOCH_OBSERVATION]')
