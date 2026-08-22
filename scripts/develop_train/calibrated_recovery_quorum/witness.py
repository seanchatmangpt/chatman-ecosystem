from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

_ALLOWED = {"PASS", "FAIL", "PENDING", "UNKNOWN", "UNSUPPORTED"}


@dataclass(frozen=True, slots=True)
class RecoveryWitness:
    attempt_id: str
    source_fingerprint: str
    outcome: str
    observed_at: datetime
    scope: str

    def __post_init__(self) -> None:
        if self.outcome not in _ALLOWED:
            raise ValueError("REFUSED[INVALID_WITNESS_OUTCOME]")
        if self.observed_at.tzinfo is None:
            raise ValueError("REFUSED[NAIVE_WITNESS_TIME]")
        if not self.attempt_id or len(self.source_fingerprint) != 64 or not self.scope:
            raise ValueError("REFUSED[INCOMPLETE_WITNESS]")
