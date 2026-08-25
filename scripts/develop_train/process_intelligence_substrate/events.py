from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .errors import Refused

@dataclass(frozen=True, order=True)
class Event:
    event_id: str
    activity: str
    occurred_at: datetime
    object_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.event_id or not self.activity:
            raise Refused("EVENT_IDENTITY")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise Refused("NAIVE_EVENT_TIME")


def canonical_trace(events: list[Event]) -> tuple[Event, ...]:
    ids = [e.event_id for e in events]
    if len(ids) != len(set(ids)):
        raise Refused("DUPLICATE_EVENT")
    return tuple(sorted(events, key=lambda e: (e.occurred_at.astimezone(timezone.utc), e.event_id)))
