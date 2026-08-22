from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from .obligation import Axis
from .subject import Subject, Refusal

class Outcome(str, Enum): PASS="PASS"; FAIL="FAIL"; PENDING="PENDING"; UNKNOWN="UNKNOWN"; UNSUPPORTED="UNSUPPORTED"

@dataclass(frozen=True)
class Witness:
    subject: Subject
    axis: Axis
    scope: str
    outcome: Outcome
    observed_at: datetime
    source: str
    def __post_init__(self):
        if self.observed_at.tzinfo is None: raise Refusal("NAIVE_TIMESTAMP")
        if self.observed_at.utcoffset() != timezone.utc.utcoffset(self.observed_at): raise Refusal("NON_UTC_TIMESTAMP")
        if not self.scope: raise Refusal("EMPTY_SCOPE")
        if not self.source: raise Refusal("EMPTY_SOURCE")
