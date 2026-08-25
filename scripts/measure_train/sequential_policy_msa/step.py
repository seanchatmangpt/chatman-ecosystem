from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .policy import PolicyIdentity
from .refusal import Refused

@dataclass(frozen=True, order=True)
class StepObservation:
    subject: Subject
    policy: PolicyIdentity
    step: int
    evidence_id: str
    predicted_bits: Fraction
    realized_bits: Fraction
    cost: Fraction
    latency_ms: Fraction
    samples: int
    observed_at: datetime
    outcome: str

    def __post_init__(self):
        if self.step < 0 or self.samples < 0:
            raise Refused("REFUSED[INVALID_STEP]")
        if not self.evidence_id.strip():
            raise Refused("REFUSED[EMPTY_EVIDENCE_ID]")
        if any(x < 0 for x in (self.predicted_bits,self.realized_bits,self.cost,self.latency_ms)):
            raise Refused("REFUSED[NEGATIVE_REALIZATION]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_OBSERVATION_TIME]")
        if self.outcome not in {"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}:
            raise Refused("REFUSED[INVALID_OUTCOME]")
