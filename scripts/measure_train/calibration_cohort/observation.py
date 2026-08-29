from dataclasses import dataclass
from datetime import datetime
from .subject import Refused
OUTCOMES={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}
@dataclass(frozen=True, order=True)
class Observation:
    source:str; epoch_generation:int; outcome:str; evidence_id:str; observed_at:datetime
    def __post_init__(self):
        if not self.source or not self.evidence_id: raise Refused("REFUSED[INVALID_OBSERVATION_IDENTITY]")
        if self.outcome not in OUTCOMES: raise Refused("REFUSED[INVALID_OUTCOME]")
        if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_OBSERVATION_TIME]")
