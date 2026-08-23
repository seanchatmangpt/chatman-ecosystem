from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class FaultTrial:
    fault:str; expected_refusal:bool; observed_refusal:bool; trial_id:str
    def __post_init__(self):
        if self.fault not in {"STALE_CAS","CORRUPT_DIGEST","ABA_TOKEN","CONCURRENT_WRITER","TRUNCATED_HISTORY","RESTART"}: raise Refused("REFUSED[UNKNOWN_FAULT]")
        if not self.trial_id: raise Refused("REFUSED[EMPTY_TRIAL_ID]")
