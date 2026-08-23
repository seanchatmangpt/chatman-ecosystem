from dataclasses import dataclass
from datetime import datetime
from .sensor import Sensor
from .subject import Refused
@dataclass(frozen=True, order=True)
class Trial:
    sensor: Sensor
    case_id: str
    truth: str
    prediction: str
    observed_at: datetime
    def __post_init__(self):
        if self.truth not in {"CURRENT","STALE"} or self.prediction not in {"CURRENT","STALE","AMBIGUOUS"}:
            raise Refused("REFUSED[INVALID_TRIAL_LABEL]")
        if not self.case_id.strip():
            raise Refused("REFUSED[EMPTY_CASE_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_TRIAL_TIME]")
