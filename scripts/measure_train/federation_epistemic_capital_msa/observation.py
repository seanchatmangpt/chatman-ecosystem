from dataclasses import dataclass
from datetime import datetime
from .subject import Subject
from .transport import Transport
from .refusal import Refused
@dataclass(frozen=True,order=True)
class TrialObservation:
    subject:Subject; transport:Transport; trial_id:str; failed:bool; predicted_current:bool; realized_current:bool; observed_at:datetime; methodology:str; engine:str; region:str; evidence_root:str
    def __post_init__(self):
        if not self.trial_id: raise Refused("REFUSED[EMPTY_TRIAL]")
        if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
        if not all((self.methodology,self.engine,self.region,self.evidence_root)): raise Refused("REFUSED[INCOMPLETE_STRATUM]")
