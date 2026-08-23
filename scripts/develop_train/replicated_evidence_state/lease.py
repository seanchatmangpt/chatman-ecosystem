from dataclasses import dataclass
from datetime import datetime, timezone
from .errors import Refused

@dataclass(frozen=True)
class Lease:
    not_before: datetime
    expires_at: datetime

    def __post_init__(self):
        if self.not_before.tzinfo is None or self.expires_at.tzinfo is None or self.not_before >= self.expires_at:
            raise Refused("INVALID_LEASE")

    def admits(self, now: datetime) -> bool:
        if now.tzinfo is None: raise Refused("NAIVE_TIME")
        return self.not_before <= now < self.expires_at
