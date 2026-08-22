from __future__ import annotations
from dataclasses import dataclass
from .admission import SubjectAdmission
from .subject import Subject

@dataclass(frozen=True)
class ClosureQuorum:
    standing: str
    admitted: tuple[Subject, ...]
    blocked: tuple[Subject, ...]

def evaluate_quorum(order: tuple[Subject, ...], admissions: dict[Subject, SubjectAdmission]) -> ClosureQuorum:
    admitted=[]; blocked=[]
    for subject in order:
        result=admissions.get(subject)
        if result is None or not result.admitted:
            blocked.append(subject)
        else:
            admitted.append(subject)
    if blocked:
        standing="BLOCKED"
    elif admitted:
        standing="PARTIAL_ALIVE"
    else:
        standing="UNKNOWN"
    return ClosureQuorum(standing, tuple(admitted), tuple(blocked))
