from dataclasses import dataclass
from datetime import datetime
from .subject import Subject
from .identity import ControlIdentity
from .refusal import Refused
@dataclass(frozen=True)
class Observation:
 subject:Subject; control:ControlIdentity; observation_id:str; result_digest:str; observed_at:datetime; state:str
 def __post_init__(self):
  if not self.observation_id or len(self.result_digest)!=64: raise Refused("REFUSED[INVALID_OBSERVATION]")
  if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
  if self.state not in {"PASS","FAIL","UNKNOWN","UNSUPPORTED","REFUSED"}: raise Refused("REFUSED[INVALID_STATE]")
