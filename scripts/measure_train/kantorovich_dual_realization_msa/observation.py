from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .certificate import Certificate
from .errors import Refused
@dataclass(frozen=True)
class CertificateObservation:
    subject: Subject
    case_id: str
    certificate: Certificate
    oracle_cost: Fraction
    realized_cost: Fraction
    implementation_id: str
    model_id: str
    observed_at: datetime
    def __post_init__(self):
        if not self.case_id or not self.implementation_id or not self.model_id: raise Refused("REFUSED[EMPTY_OBSERVATION_IDENTITY]")
        if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
