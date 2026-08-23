from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject, Refused
from .bound import RobustnessBound
@dataclass(frozen=True, order=True)
class BoundCase:
    subject: Subject
    bound: RobustnessBound
    truth: Fraction
    evidence_id: str
    observed_at: datetime
    def __post_init__(self):
        if not self.evidence_id: raise Refused("REFUSED[EMPTY_EVIDENCE_ID]")
        if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
    @property
    def covers(self): return self.bound.lower <= self.truth <= self.bound.upper
