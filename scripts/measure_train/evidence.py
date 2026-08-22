from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from datetime import datetime
from .identity import Subject, Standing
from .window import parse_time

class EvidenceKind(StrEnum):
    COMMIT="commit"; PR="pull_request"; CI="ci"; ARTIFACT="artifact"; RUNTIME="runtime"; DEPENDENCY="dependency"; RECEIPT="receipt"; BLOCKER="blocker"
class Outcome(StrEnum):
    PASS="PASS"; FAIL="FAIL"; PENDING="PENDING"; UNKNOWN="UNKNOWN"; UNSUPPORTED="UNSUPPORTED"

@dataclass(frozen=True, order=True)
class Evidence:
    source_id: str
    subject: Subject
    kind: EvidenceKind
    observed_at: datetime
    outcome: Outcome
    digest: str=""
    detail: str=""
    def __post_init__(self): object.__setattr__(self,"observed_at",parse_time(self.observed_at))
    def standing(self)->Standing:
        if self.outcome==Outcome.FAIL: return Standing.BUILD_BROKEN
        if self.outcome in (Outcome.PENDING,Outcome.UNKNOWN): return Standing.UNKNOWN
        if self.outcome==Outcome.UNSUPPORTED: return Standing.UNSUPPORTED
        return Standing.PARTIAL_ALIVE
