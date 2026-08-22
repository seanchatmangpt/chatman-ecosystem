from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .subject import Subject

STATES = ("DELIVERED","ACKNOWLEDGED","DISCHARGED")
DISCHARGE_RESULTS = frozenset({"REQUALIFIED","BLOCKED","UNSUPPORTED"})

class WitnessRefusal(ValueError):
    pass

def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise WitnessRefusal("REFUSED[NAIVE_WITNESS_TIME]")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True)
class Witness:
    consumer: Subject
    event_id: str
    state: str
    at: datetime
    result: str | None = None

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise WitnessRefusal("REFUSED[UNKNOWN_WITNESS_STATE]")
        object.__setattr__(self, "at", _utc(self.at))
        if self.state == "DISCHARGED":
            if self.result not in DISCHARGE_RESULTS:
                raise WitnessRefusal("REFUSED[UNBOUNDED_DISCHARGE_RESULT]")
        elif self.result is not None:
            raise WitnessRefusal("REFUSED[PREMATURE_DISCHARGE_RESULT]")
