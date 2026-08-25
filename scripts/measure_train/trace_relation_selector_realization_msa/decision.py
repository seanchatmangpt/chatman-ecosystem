from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
from .selector import SelectorIdentity
from .relation import Relation

@dataclass(frozen=True, order=True)
class Decision:
    subject: Subject
    selector: SelectorIdentity
    decision_id: str
    chosen: tuple[Relation, ...]
    candidates: tuple[Relation, ...]
    predicted_error_ppm: int
    evaluation_cost_micros: int
    decided_at: datetime

    def __post_init__(self):
        if not self.decision_id:
            raise Refused("REFUSED[EMPTY_DECISION_ID]")
        if self.decided_at.tzinfo is None or self.decided_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_DECISION_TIME]")
        if not self.chosen or not set(self.chosen) <= set(self.candidates):
            raise Refused("REFUSED[INVALID_SELECTION_SET]")
        if len(set(self.candidates)) != len(self.candidates):
            raise Refused("REFUSED[DUPLICATE_CANDIDATE]")
        if not (0 <= self.predicted_error_ppm <= 1_000_000):
            raise Refused("REFUSED[INVALID_PREDICTED_ERROR]")
        if self.evaluation_cost_micros < 0:
            raise Refused("REFUSED[INVALID_EVALUATION_COST]")
