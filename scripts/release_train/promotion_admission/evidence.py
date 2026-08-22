from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from .subject import Subject

class Axis(str, Enum):
    FOCUSED="FOCUSED"; REPOSITORY="REPOSITORY"; RUNTIME="RUNTIME"
    ARTIFACT="ARTIFACT"; DEPENDENCY="DEPENDENCY"; RECEIPT="RECEIPT"

class Outcome(str, Enum):
    PASS="PASS"; FAIL="FAIL"; PENDING="PENDING"; UNKNOWN="UNKNOWN"; UNSUPPORTED="UNSUPPORTED"

class EvidenceRefusal(ValueError):
    pass

@dataclass(frozen=True)
class Evidence:
    subject: Subject
    axis: Axis
    outcome: Outcome
    observed_at: datetime
    source: str

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise EvidenceRefusal("REFUSED[NAIVE_EVIDENCE_TIME]")
        if not self.source.strip():
            raise EvidenceRefusal("REFUSED[EMPTY_EVIDENCE_SOURCE]")

def normalize_vector(subject: Subject, rows: list[Evidence]) -> dict[Axis, Outcome]:
    vector: dict[Axis, Outcome] = {}
    for row in rows:
        if row.subject != subject:
            raise EvidenceRefusal("REFUSED[FOREIGN_SUBJECT_EVIDENCE]")
        previous = vector.get(row.axis)
        if previous is not None and previous != row.outcome:
            raise EvidenceRefusal("REFUSED[CONTRADICTORY_AXIS_EVIDENCE]")
        vector[row.axis] = row.outcome
    return dict(sorted(vector.items(), key=lambda item: item[0].value))
