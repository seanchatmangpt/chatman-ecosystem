from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

KINDS={"NEW_HEAD","NEW_RECEIPT","SCHEMA_CHANGE","EXPIRED","BUILD_BROKEN","BLOCKED","RECOVERED"}

@dataclass(frozen=True, order=True)
class InvalidationEvent:
    producer: Subject
    kind: str
    observed_at: datetime
    event_id: str
    replacement_receipt: str | None = None
    def __post_init__(self):
        if self.kind not in KINDS:
            raise Refused("REFUSED[UNKNOWN_INVALIDATION_KIND]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_EVENT_TIME]")
        if not self.event_id.strip():
            raise Refused("REFUSED[EMPTY_EVENT_ID]")
        if self.replacement_receipt is not None and len(self.replacement_receipt) != 64:
            raise Refused("REFUSED[INVALID_REPLACEMENT_RECEIPT]")
