from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

class WindowRefusal(ValueError):
    pass

def parse_utc(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WindowRefusal("REFUSED[INVALID_TIMESTAMP]") from exc
    if dt.tzinfo is None:
        raise WindowRefusal("REFUSED[NAIVE_TIMESTAMP]")
    return dt.astimezone(timezone.utc)

@dataclass(frozen=True)
class ObservationWindow:
    since: datetime
    until: datetime

    @classmethod
    def admit(cls, since: str, until: str) -> "ObservationWindow":
        left, right = parse_utc(since), parse_utc(until)
        if left >= right:
            raise WindowRefusal("REFUSED[INVALID_OBSERVATION_WINDOW]")
        return cls(left, right)

    def contains(self, timestamp: str) -> bool:
        t = parse_utc(timestamp)
        return self.since <= t < self.until
