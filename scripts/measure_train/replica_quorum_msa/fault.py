from dataclasses import dataclass
from .subject import Refused
FAULTS={"HEALTHY","PARTITION","STALE_REPLICA","SPLIT_BRAIN","OMISSION","CLOCK_SKEW"}
@dataclass(frozen=True, order=True)
class FaultTrial:
    trial_id:str; truth:str; predicted:str
    def __post_init__(self):
        if not self.trial_id: raise Refused("REFUSED[EMPTY_TRIAL_ID]")
        if self.truth not in FAULTS: raise Refused("REFUSED[UNKNOWN_TRUTH_CLASS]")
        if self.predicted not in {"CURRENT","NOT_CURRENT","AMBIGUOUS"}: raise Refused("REFUSED[INVALID_SENSOR_PREDICTION]")
