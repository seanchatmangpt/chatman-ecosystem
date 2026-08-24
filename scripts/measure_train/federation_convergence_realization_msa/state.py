from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .refusals import Refused
ALLOWED={'CONVERGING','FIXED','OSCILLATING','STALLED','REGRESSING','UNKNOWN'}
@dataclass(frozen=True, order=True)
class Observation:
    subject:Subject; observation_id:str; state:str; blocker_count:int; error_mass:Fraction; churn_mass:Fraction; observed_at:datetime; predicted_fixed:bool=False
    def __post_init__(self):
        if not self.observation_id: raise Refused('REFUSED[EMPTY_OBSERVATION_ID]')
        if self.state not in ALLOWED: raise Refused('REFUSED[INVALID_CONVERGENCE_STATE]')
        if self.blocker_count<0 or self.error_mass<0 or self.churn_mass<0: raise Refused('REFUSED[NEGATIVE_CONVERGENCE_MASS]')
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused('REFUSED[NAIVE_TIME]')
