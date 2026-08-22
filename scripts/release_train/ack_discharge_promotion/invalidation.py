from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .subject import Subject

KINDS = frozenset({"NEW_HEAD","NEW_RECEIPT","SCHEMA_CHANGE","EXPIRED","BUILD_BROKEN","BLOCKED","RECOVERED"})

class InvalidationRefusal(ValueError):
    pass

def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidationRefusal("REFUSED[NAIVE_TIME]")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True)
class Invalidation:
    producer: Subject
    event_id: str
    kind: str
    at: datetime
    replacement_receipt: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise InvalidationRefusal("REFUSED[UNKNOWN_INVALIDATION_KIND]")
        object.__setattr__(self, "at", _utc(self.at))
        if self.kind == "NEW_RECEIPT":
            if self.replacement_receipt is None or len(self.replacement_receipt) != 64:
                raise InvalidationRefusal("REFUSED[MISSING_REPLACEMENT_RECEIPT]")
