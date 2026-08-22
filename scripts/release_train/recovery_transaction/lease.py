from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .subject import Refusal

@dataclass(frozen=True)
class Lease:
    not_before: datetime
    expires_at: datetime
    def __post_init__(self) -> None:
        if self.not_before.tzinfo is None or self.expires_at.tzinfo is None or not self.not_before < self.expires_at:
            raise Refusal("REFUSED[INVALID_RECOVERY_LEASE]")
    def active(self, at: datetime) -> bool:
        if at.tzinfo is None:
            raise Refusal("REFUSED[NAIVE_RECOVERY_TIME]")
        return self.not_before <= at < self.expires_at
