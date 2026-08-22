from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .epoch import ProducerEpoch
from .identity import Refusal
@dataclass(frozen=True, slots=True)
class EvidenceCut:
    cut_id: str
    generation: int
    epochs: tuple[ProducerEpoch, ...]
    valid_from: datetime
    valid_until: datetime
    def __post_init__(self) -> None:
        if self.generation < 0:
            raise Refusal("REFUSED[INVALID_CUT_GENERATION]")
        if not self.cut_id:
            raise Refusal("REFUSED[EMPTY_CUT_ID]")
        if not self.epochs:
            raise Refusal("REFUSED[EMPTY_CUT]")
        repos = [e.subject.repository for e in self.epochs]
        if len(repos) != len(set(repos)):
            raise Refusal("REFUSED[DUPLICATE_CUT_PRODUCER]")
        if self.valid_from.tzinfo is None or self.valid_until.tzinfo is None:
            raise Refusal("REFUSED[NAIVE_CUT_LEASE]")
        if self.valid_until <= self.valid_from:
            raise Refusal("REFUSED[INVALID_CUT_LEASE]")
    def epoch_map(self) -> dict[str, ProducerEpoch]:
        return {e.subject.repository: e for e in self.epochs}
