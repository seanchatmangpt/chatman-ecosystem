from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class CutCandidate:
    cut_id: str
    consumer: Subject
    producer_receipt_digest: str
    generation: int
    observed_at: datetime
    complete: bool

    def __post_init__(self):
        if len(self.cut_id) != 64 or any(c not in "0123456789abcdef" for c in self.cut_id):
            raise Refused("REFUSED[INVALID_CUT_ID]")
        if len(self.producer_receipt_digest) != 64 or any(c not in "0123456789abcdef" for c in self.producer_receipt_digest):
            raise Refused("REFUSED[INVALID_PRODUCER_RECEIPT_DIGEST]")
        if self.generation < 0:
            raise Refused("REFUSED[INVALID_CUT_GENERATION]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_CANDIDATE_TIME]")
