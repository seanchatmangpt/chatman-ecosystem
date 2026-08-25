from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .stress import StressIdentity
from .refusal import Refused
@dataclass(frozen=True, order=True)
class RealizationCase:
    subject: Subject
    stress: StressIdentity
    predicted_invariant: bool
    predicted_risk: Fraction
    observed_success: bool
    observed_risk: Fraction
    methodology: str
    engine: str
    region: str
    evidence_root: str
    case_id: str
    observed_at: datetime
    def __post_init__(self):
        if not self.case_id: raise Refused("REFUSED[EMPTY_CASE_ID]")
        if not (Fraction(0)<=self.predicted_risk<=Fraction(1)): raise Refused("REFUSED[INVALID_PREDICTED_RISK]")
        if not (Fraction(0)<=self.observed_risk<=Fraction(1)): raise Refused("REFUSED[INVALID_OBSERVED_RISK]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_REALIZATION_TIME]")
        if not all((self.methodology,self.engine,self.region,self.evidence_root)): raise Refused("REFUSED[INCOMPLETE_REALIZATION_STRATUM]")
