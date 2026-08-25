from dataclasses import dataclass
from datetime import datetime
from .projection import Projection
from .refusal import Refused
@dataclass(frozen=True, order=True)
class ProjectionObservation:
    projection:Projection; observed_at:datetime; state:str; oracle_label:str
    def __post_init__(self):
        if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
        if self.state not in {"PASS","FAIL","UNKNOWN","UNSUPPORTED","REFUSED"}: raise Refused("REFUSED[INVALID_STATE]")
        if self.oracle_label not in {"EQUIVALENT","DIVERGED","UNKNOWN"}: raise Refused("REFUSED[INVALID_ORACLE_LABEL]")
