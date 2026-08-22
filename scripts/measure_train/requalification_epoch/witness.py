from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

KINDS={"DELIVERY","ACKNOWLEDGEMENT","DISCHARGE","RECOVERY"}
OUTCOMES={"OBSERVED","REQUALIFIED","BLOCKED","UNSUPPORTED"}

@dataclass(frozen=True, order=True)
class Witness:
    consumer: Subject
    producer: Subject
    generation: int
    event_id: str
    kind: str
    witness_id: str
    observed_at: datetime
    outcome: str = "OBSERVED"
    parent_id: str | None = None
    receipt_sha256: str | None = None
    def __post_init__(self):
        if self.generation < 0: raise Refused("REFUSED[INVALID_WITNESS_GENERATION]")
        if self.kind not in KINDS: raise Refused("REFUSED[INVALID_WITNESS_KIND]")
        if self.outcome not in OUTCOMES: raise Refused("REFUSED[INVALID_WITNESS_OUTCOME]")
        if not self.witness_id or not self.event_id: raise Refused("REFUSED[EMPTY_WITNESS_IDENTITY]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_WITNESS_TIME]")
        if self.kind in {"DISCHARGE","RECOVERY"} and self.outcome == "OBSERVED": raise Refused("REFUSED[UNBOUNDED_TERMINAL_WITNESS]")
        if self.receipt_sha256 is not None and (len(self.receipt_sha256)!=64 or any(c not in "0123456789abcdef" for c in self.receipt_sha256)):
            raise Refused("REFUSED[INVALID_WITNESS_RECEIPT]")
