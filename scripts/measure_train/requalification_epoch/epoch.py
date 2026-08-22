from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class InvalidationEpoch:
    producer: Subject
    generation: int
    event_id: str
    observed_at: datetime
    receipt_sha256: str
    def __post_init__(self):
        if self.generation < 0:
            raise Refused("REFUSED[INVALID_GENERATION]")
        if not self.event_id.strip():
            raise Refused("REFUSED[EMPTY_EVENT_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_EPOCH_TIME]")
        if len(self.receipt_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.receipt_sha256):
            raise Refused("REFUSED[INVALID_EPOCH_RECEIPT]")
