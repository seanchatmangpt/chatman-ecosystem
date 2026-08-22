from dataclasses import dataclass
from datetime import datetime
from .subject import Refused
from .case import DetectorCase
from .policy import DetectorPolicy

@dataclass(frozen=True, order=True)
class DetectorRun:
    case_id: str
    policy_fingerprint: str
    observed_at: datetime
    alarm_at: datetime | None
    evidence_id: str

    def __post_init__(self):
        if self.observed_at.tzinfo is None or (self.alarm_at is not None and self.alarm_at.tzinfo is None):
            raise Refused("REFUSED[NAIVE_RUN_TIME]")
        if not self.evidence_id:
            raise Refused("REFUSED[EMPTY_RUN_EVIDENCE]")

def admit_run(case: DetectorCase, policy: DetectorPolicy, run: DetectorRun):
    if run.case_id != case.case_id or run.policy_fingerprint != policy.fingerprint:
        raise Refused("REFUSED[FOREIGN_DETECTOR_RUN]")
    if run.observed_at < case.end:
        raise Refused("REFUSED[INCOMPLETE_DETECTOR_RUN]")
    if run.alarm_at is not None:
        if not (case.start <= run.alarm_at < case.end):
            raise Refused("REFUSED[ALARM_OUTSIDE_CASE_WINDOW]")
        if case.transition_at is not None and run.alarm_at < case.transition_at:
            raise Refused("REFUSED[PRETRANSITION_ALARM]")
    return run
