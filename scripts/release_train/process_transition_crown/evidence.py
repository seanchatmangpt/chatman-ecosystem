from dataclasses import dataclass
from datetime import datetime, timezone
from .refusal import Refused
from .subject import SubjectEpoch
from .obligation import State

@dataclass(frozen=True)
class Evidence:
    subject: SubjectEpoch
    obligation: str
    source: str
    outcome: State
    observed_at: datetime
    digest: str

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise Refused("NAIVE_EVIDENCE_TIME")
        if not self.source or not self.digest:
            raise Refused("MALFORMED_EVIDENCE")

def admit(evidence: Evidence, expected: SubjectEpoch, now: datetime, max_age_seconds: int) -> Evidence:
    if evidence.subject != expected:
        raise Refused("FOREIGN_OR_STALE_SUBJECT")
    now = now.astimezone(timezone.utc)
    seen = evidence.observed_at.astimezone(timezone.utc)
    age = (now - seen).total_seconds()
    if age < 0:
        raise Refused("EVIDENCE_FROM_FUTURE")
    if age > max_age_seconds:
        raise Refused("EVIDENCE_STALE")
    return evidence
