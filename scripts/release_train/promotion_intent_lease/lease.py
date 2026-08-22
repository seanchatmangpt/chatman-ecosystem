from dataclasses import dataclass
from datetime import datetime
from .subject import Refusal

@dataclass(frozen=True)
class IntentLease:
    not_before: datetime
    expires_at: datetime

    def __post_init__(self):
        if self.not_before.tzinfo is None or self.expires_at.tzinfo is None or self.not_before >= self.expires_at:
            raise Refusal('REFUSED[INVALID_INTENT_LEASE]')

    def active(self, now: datetime) -> bool:
        if now.tzinfo is None:
            raise Refusal('REFUSED[NAIVE_TIME]')
        return self.not_before <= now < self.expires_at
