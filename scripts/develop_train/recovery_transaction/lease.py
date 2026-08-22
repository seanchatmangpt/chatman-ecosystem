from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .subject import Refusal

def _aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.utcoffset() is not None

@dataclass(frozen=True)
class Lease:
    not_before: datetime
    expires_at: datetime
    def __post_init__(self) -> None:
        if not _aware(self.not_before) or not _aware(self.expires_at):
            raise Refusal("NAIVE_LEASE_TIME", "lease times must be timezone-aware")
        if self.expires_at <= self.not_before:
            raise Refusal("INVALID_LEASE", "expires_at must be after not_before")
    def active(self, now: datetime) -> bool:
        if not _aware(now):
            raise Refusal("NAIVE_LEASE_TIME", "now must be timezone-aware")
        return self.not_before <= now < self.expires_at
