from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
from .relation import Relation

@dataclass(frozen=True, order=True)
class LabeledCase:
    subject: Subject
    case_id: str
    relation: Relation
    expected: bool
    observed: bool
    perturbation: str
    oracle_impl: str
    observed_at: datetime
    def __post_init__(self):
        if not self.case_id or not self.perturbation or not self.oracle_impl:
            raise Refused("REFUSED[EMPTY_CASE_IDENTITY]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_CASE_TIME]")
