from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .identity import Refusal, Subject
@dataclass(frozen=True, slots=True)
class ProducerEpoch:
    subject: Subject
    generation: int
    receipt: str
    observed_at: datetime
    def __post_init__(self) -> None:
        if self.generation < 0:
            raise Refusal("REFUSED[INVALID_GENERATION]")
        if len(self.receipt) != 64 or any(c not in "0123456789abcdef" for c in self.receipt):
            raise Refusal("REFUSED[INVALID_EPOCH_RECEIPT]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refusal("REFUSED[NAIVE_EPOCH_TIME]")
