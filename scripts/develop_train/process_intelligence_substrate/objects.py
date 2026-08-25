from __future__ import annotations
from dataclasses import dataclass
from .events import Event
from .errors import Refused

@dataclass(frozen=True)
class ObjectTrace:
    object_id: str
    events: tuple[Event, ...]


def object_centric(events: tuple[Event, ...]) -> tuple[ObjectTrace, ...]:
    buckets: dict[str, list[Event]] = {}
    for event in events:
        if not event.object_ids:
            raise Refused("EVENT_WITHOUT_OBJECT", event.event_id)
        for oid in event.object_ids:
            buckets.setdefault(oid, []).append(event)
    return tuple(ObjectTrace(oid, tuple(items)) for oid, items in sorted(buckets.items()))


def shared_identity(event_view: tuple[Event, ...], object_view: tuple[ObjectTrace, ...]) -> bool:
    left = {e.event_id for e in event_view}
    right = {e.event_id for trace in object_view for e in trace.events}
    return left == right
