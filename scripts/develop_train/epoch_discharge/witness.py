from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from .identity import Subject

_HEX64 = re.compile(r"^[0-9a-f]{64}$")

class WitnessKind(str, Enum):
    DELIVERY="DELIVERY"
    ACK="ACK"
    DISCHARGE="DISCHARGE"

class DischargeResult(str, Enum):
    REQUALIFIED="REQUALIFIED"
    BLOCKED="BLOCKED"
    UNSUPPORTED="UNSUPPORTED"

@dataclass(frozen=True, slots=True)
class Witness:
    producer: Subject
    consumer: Subject
    generation: int
    event_id: str
    kind: WitnessKind
    witness_id: str
    receipt_digest: str
    observed_at: datetime
    parent_receipt: str|None=None
    result: DischargeResult|None=None
    def __post_init__(self)->None:
        if self.generation < 0: raise ValueError("REFUSED[INVALID_WITNESS_GENERATION]")
        if not self.event_id.strip() or not self.witness_id.strip(): raise ValueError("REFUSED[EMPTY_WITNESS_ID]")
        if not _HEX64.fullmatch(self.receipt_digest): raise ValueError("REFUSED[INVALID_WITNESS_RECEIPT]")
        if self.parent_receipt is not None and not _HEX64.fullmatch(self.parent_receipt): raise ValueError("REFUSED[INVALID_PARENT_RECEIPT]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise ValueError("REFUSED[NAIVE_WITNESS_TIME]")
        if self.kind is WitnessKind.DELIVERY and self.parent_receipt is not None: raise ValueError("REFUSED[DELIVERY_PARENT_FORBIDDEN]")
        if self.kind is not WitnessKind.DISCHARGE and self.result is not None: raise ValueError("REFUSED[RESULT_ON_NON_DISCHARGE]")
        if self.kind is WitnessKind.DISCHARGE and self.result is None: raise ValueError("REFUSED[MISSING_DISCHARGE_RESULT]")
