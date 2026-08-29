from dataclasses import dataclass
from datetime import datetime, timezone

from .subject import Refusal


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise Refusal('REFUSED[NAIVE_TIME]')
    return value.astimezone(timezone.utc)

@dataclass(frozen=True)
class CalibrationWindow:
    since: datetime
    until: datetime

    def __post_init__(self) -> None:
        since, until = utc(self.since), utc(self.until)
        if since >= until:
            raise Refusal('REFUSED[INVALID_WINDOW]')
        object.__setattr__(self, 'since', since)
        object.__setattr__(self, 'until', until)

    def contains(self, when: datetime) -> bool:
        when = utc(when)
        return self.since <= when < self.until
