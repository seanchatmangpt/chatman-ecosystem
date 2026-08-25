from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
from .source import Source
OUTCOMES={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}
@dataclass(frozen=True, order=True)
class Claim:
    subject: Subject
    source: Source
    observed_at: datetime
    outcome: str
    evidence_id: str
    def __post_init__(self):
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_TIME]")
        if self.outcome not in OUTCOMES: raise Refused("REFUSED[INVALID_OUTCOME]")
        if not self.evidence_id: raise Refused("REFUSED[EMPTY_EVIDENCE_ID]")
