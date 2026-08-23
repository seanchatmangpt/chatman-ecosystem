from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
@dataclass(frozen=True, order=True)
class IndependenceTrial:
    subject:Subject; pair_id:str; predicted:str; truth:str; observed_at:datetime
    def __post_init__(self):
        if self.predicted not in {"INDEPENDENT","DEPENDENT"} or self.truth not in {"INDEPENDENT","DEPENDENT"}: raise Refused("REFUSED[INVALID_TRIAL_LABEL]")
        if not self.pair_id or self.observed_at.tzinfo is None: raise Refused("REFUSED[INVALID_TRIAL_IDENTITY]")
