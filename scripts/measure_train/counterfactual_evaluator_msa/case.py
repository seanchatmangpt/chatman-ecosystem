from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .estimator import EstimatorIdentity
from .refusal import Refused

@dataclass(frozen=True, order=True)
class EvaluationCase:
    subject: Subject
    estimator: EstimatorIdentity
    case_id: str
    truth: Fraction
    estimate: Fraction
    behavior_propensity: Fraction
    target_propensity: Fraction
    observed_at: datetime
    def __post_init__(self):
        if not self.case_id.strip(): raise Refused("REFUSED[EMPTY_CASE_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_CASE_TIME]")
        if self.behavior_propensity <= 0 or self.behavior_propensity > 1: raise Refused("REFUSED[POSITIVITY_VIOLATION]")
        if self.target_propensity < 0 or self.target_propensity > 1: raise Refused("REFUSED[INVALID_TARGET_PROPENSITY]")
