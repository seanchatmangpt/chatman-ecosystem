from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject, Refused

OUTCOMES={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}

@dataclass(frozen=True, order=True)
class AcquisitionOutcome:
    subject: Subject
    plan_id: str
    candidate_id: str
    observed_at: datetime
    outcome: str
    posterior_defect: Fraction
    actual_cost: Fraction
    actual_latency_ms: int
    evidence_id: str

    def __post_init__(self):
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_OUTCOME_TIME]")
        if self.outcome not in OUTCOMES:
            raise Refused("REFUSED[INVALID_OUTCOME]")
        if not (Fraction(0) <= self.posterior_defect <= Fraction(1)):
            raise Refused("REFUSED[INVALID_POSTERIOR]")
        if self.actual_cost < 0 or self.actual_latency_ms < 0:
            raise Refused("REFUSED[INVALID_ACTUAL_RESOURCE]")
        if not self.evidence_id:
            raise Refused("REFUSED[EMPTY_EVIDENCE_ID]")
