from dataclasses import dataclass
from fractions import Fraction
from .subject import Subject, Refused
from .interval import Interval
@dataclass(frozen=True, order=True)
class CompositionCase:
    subject: Subject
    case_id: str
    predicted: Interval
    truth: Fraction
    mode: str
    def __post_init__(self):
        if not self.case_id: raise Refused("REFUSED[EMPTY_CASE_ID]")
        if self.truth<0 or self.truth>1: raise Refused("REFUSED[INVALID_TRUTH]")
    @property
    def covered(self): return self.predicted.contains(self.truth)
