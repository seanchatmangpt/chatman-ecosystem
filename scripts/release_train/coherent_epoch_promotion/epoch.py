from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import re
from .subject import Subject

_HEX64 = re.compile(r'^[0-9a-f]{64}$')

@dataclass(frozen=True)
class EpochStamp:
    producer: Subject
    generation: int
    event_id: str
    receipt: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if self.generation < 0:
            raise ValueError('REFUSED[INVALID_GENERATION]')
        if not self.event_id:
            raise ValueError('REFUSED[MISSING_EVENT_ID]')
        if not _HEX64.fullmatch(self.receipt):
            raise ValueError('REFUSED[INVALID_EPOCH_RECEIPT]')
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError('REFUSED[NAIVE_EPOCH_TIME]')

    def identity(self) -> tuple[str, int, str, str]:
        return (self.producer.key(), self.generation, self.event_id, self.receipt)
