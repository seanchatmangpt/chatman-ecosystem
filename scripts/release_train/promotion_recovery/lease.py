from dataclasses import dataclass
from datetime import datetime
from .subject import Refusal

@dataclass(frozen=True)
class IntentLease:
    issued_at: datetime
    expires_at: datetime
    def __post_init__(self):
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None or self.expires_at <= self.issued_at:
            raise Refusal('REFUSED[INVALID_INTENT_LEASE]')
    def active(self, now):
        if now.tzinfo is None: raise Refusal('REFUSED[NAIVE_TIME]')
        return self.issued_at <= now < self.expires_at
