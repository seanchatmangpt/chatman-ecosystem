from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from .identity import Subject

_HEX64 = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True, slots=True)
class InvalidationEpoch:
    producer: Subject
    generation: int
    event_id: str
    receipt_digest: str
    observed_at: datetime
    def __post_init__(self) -> None:
        if self.generation < 0:
            raise ValueError("REFUSED[INVALID_GENERATION]")
        if not self.event_id.strip():
            raise ValueError("REFUSED[EMPTY_EVENT_ID]")
        if not _HEX64.fullmatch(self.receipt_digest):
            raise ValueError("REFUSED[INVALID_EPOCH_RECEIPT]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("REFUSED[NAIVE_EPOCH_TIME]")
        if self.observed_at > datetime.now(timezone.utc):
            raise ValueError("REFUSED[FUTURE_EPOCH]")
    @property
    def key(self) -> tuple[str, int, str]:
        return (self.producer.value, self.generation, self.event_id)
