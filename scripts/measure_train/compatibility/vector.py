from dataclasses import dataclass
from .subject_vector import Subject
from .evidence_axis import Axis, Outcome
@dataclass(frozen=True)
class Evidence:
    subject: Subject
    axis: Axis
    outcome: Outcome
    observed_at: str
@dataclass(frozen=True)
class EvidenceVector:
    subject: Subject
    rows: tuple[Evidence,...]
    def __post_init__(self):
        if any(r.subject != self.subject for r in self.rows):
            raise ValueError("REFUSED[FOREIGN_VECTOR_ROW]")
