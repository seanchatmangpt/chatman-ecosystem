from dataclasses import dataclass
from datetime import datetime, timezone
from .refusal import Refused
@dataclass(frozen=True)
class Lease:
    not_before: datetime
    expires_at: datetime
    def __post_init__(self):
        if self.not_before.tzinfo is None or self.expires_at.tzinfo is None: raise Refused("NAIVE_LEASE")
        if self.not_before >= self.expires_at: raise Refused("INVALID_LEASE")
    def admits(self, at: datetime) -> bool:
        if at.tzinfo is None: raise Refused("NAIVE_OBSERVATION_TIME")
        at=at.astimezone(timezone.utc)
        return self.not_before.astimezone(timezone.utc) <= at < self.expires_at.astimezone(timezone.utc)
