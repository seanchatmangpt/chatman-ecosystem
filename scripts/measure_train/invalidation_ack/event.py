from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

KINDS={"NEW_HEAD","NEW_RECEIPT","SCHEMA_CHANGE","EXPIRED","BUILD_BROKEN","BLOCKED","RECOVERED"}

@dataclass(frozen=True, order=True)
class Invalidation:
    producer: Subject
    event_id: str
    kind: str
    observed_at: datetime
    replacement_receipt: str | None = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise Refused("REFUSED[UNKNOWN_INVALIDATION_KIND]")
        if not self.event_id.strip():
            raise Refused("REFUSED[EMPTY_EVENT_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_EVENT_TIME]")
        if self.kind == "NEW_RECEIPT" and not self.replacement_receipt:
            raise Refused("REFUSED[MISSING_REPLACEMENT_RECEIPT]")
        if self.replacement_receipt is not None:
            if len(self.replacement_receipt) != 64 or any(c not in "0123456789abcdef" for c in self.replacement_receipt):
                raise Refused("REFUSED[INVALID_REPLACEMENT_RECEIPT]")
