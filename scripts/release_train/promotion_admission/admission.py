from __future__ import annotations
from dataclasses import dataclass
from .evidence import Axis, Outcome
from .requirements import ReleaseProfile, evaluate_profile
from .subject import Subject

@dataclass(frozen=True)
class SubjectAdmission:
    subject: Subject
    admitted: bool
    reasons: tuple[str, ...]

def admit_subject(subject: Subject, vector: dict[Axis, Outcome], profile: ReleaseProfile) -> SubjectAdmission:
    ok, missing = evaluate_profile(vector, profile)
    reasons: list[str] = []
    if missing:
        reasons.append("MISSING_AXES:" + ",".join(axis.value for axis in missing))
    failures = tuple(sorted(axis.value for axis, out in vector.items() if out == Outcome.FAIL))
    pending = tuple(sorted(axis.value for axis, out in vector.items() if out == Outcome.PENDING))
    if failures:
        reasons.append("FAILED_AXES:" + ",".join(failures))
    if pending:
        reasons.append("PENDING_AXES:" + ",".join(pending))
    if not ok and not reasons:
        reasons.append("PROFILE_OUTCOME_NOT_ADMITTED")
    return SubjectAdmission(subject, ok, tuple(reasons))
