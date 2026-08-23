from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .distribution import Distribution
from .ambiguity import AmbiguityModel
from .refusal import Refused
@dataclass(frozen=True, order=True)
class RealizationObservation:
    subject: Subject
    observation_id: str
    model: AmbiguityModel
    target: Distribution
    realized_loss: Fraction
    predicted_worst_loss: Fraction
    witness_loss: Fraction|None
    methodology: str
    engine: str
    region: str
    evidence_root: str
    observed_at: datetime
    def __post_init__(self):
        if not self.observation_id: raise Refused("REFUSED[EMPTY_OBSERVATION_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_OBSERVATION_TIME]")
        if self.realized_loss < 0 or self.predicted_worst_loss < 0: raise Refused("REFUSED[NEGATIVE_LOSS]")
