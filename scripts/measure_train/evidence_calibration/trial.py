from dataclasses import dataclass
from datetime import datetime
from .subject import Refused
@dataclass(frozen=True, order=True)
class CalibrationTrial:
    source_id:str
    trial_id:str
    predicted_positive:bool
    truth_positive:bool
    observed_at:datetime
    def __post_init__(self):
        if not self.source_id or not self.trial_id: raise Refused("REFUSED[EMPTY_TRIAL_IDENTITY]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_TRIAL_TIME]")
