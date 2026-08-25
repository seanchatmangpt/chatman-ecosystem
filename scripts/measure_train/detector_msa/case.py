from dataclasses import dataclass
from datetime import datetime
from .subject import Refused

@dataclass(frozen=True, order=True)
class DetectorCase:
    case_id: str
    source_id: str
    start: datetime
    end: datetime
    transition_at: datetime | None = None

    def __post_init__(self):
        if not self.case_id or not self.source_id:
            raise Refused("REFUSED[EMPTY_CASE_IDENTITY]")
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise Refused("REFUSED[NAIVE_CASE_TIME]")
        if self.end <= self.start:
            raise Refused("REFUSED[INVALID_CASE_WINDOW]")
        if self.transition_at is not None and not (self.start <= self.transition_at < self.end):
            raise Refused("REFUSED[TRANSITION_OUTSIDE_HALF_OPEN_WINDOW]")
