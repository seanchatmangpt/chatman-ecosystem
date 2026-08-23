from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
from .relation import Relation

@dataclass(frozen=True, order=True)
class RealizedRelation:
    subject: Subject
    decision_id: str
    relation: Relation
    equivalent: bool
    realized_cost_micros: int
    observed_at: datetime
    source_id: str

    def __post_init__(self):
        if not self.decision_id or not self.source_id:
            raise Refused("REFUSED[EMPTY_REALIZATION_IDENTITY]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_REALIZATION_TIME]")
        if self.realized_cost_micros < 0:
            raise Refused("REFUSED[INVALID_REALIZED_COST]")
