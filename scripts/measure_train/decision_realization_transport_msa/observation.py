from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .stratum import Stratum
from .errors import Refused
@dataclass(frozen=True,order=True)
class Observation:
    subject:Subject; observation_id:str; stratum:Stratum; realized_loss:Fraction; predicted_risk:Fraction
    observed:bool; observed_at:datetime
    def __post_init__(self):
        if not self.observation_id: raise Refused("REFUSED[EMPTY_OBSERVATION_ID]")
        if not (0<=self.realized_loss<=1 and 0<=self.predicted_risk<=1): raise Refused("REFUSED[NON_UNIT_RISK]")
        if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
