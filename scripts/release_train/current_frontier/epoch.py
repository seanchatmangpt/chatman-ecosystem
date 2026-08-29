from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

class Refusal(ValueError):
    pass

def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise Refusal("REFUSED[NAIVE_TIME]")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True)
class Epoch:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        start, end = _utc(self.start), _utc(self.end)
        if not start < end:
            raise Refusal("REFUSED[INVALID_EPOCH]")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    def contains(self, when: datetime) -> bool:
        when = _utc(when)
        return self.start <= when < self.end
