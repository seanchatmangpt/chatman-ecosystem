from dataclasses import dataclass
from datetime import datetime
@dataclass(frozen=True)
class EvidenceLease:
    issued_at:datetime
    expires_at:datetime
    def __post_init__(self):
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("REFUSED[NAIVE_LEASE]")
        if self.expires_at <= self.issued_at:
            raise ValueError("REFUSED[INVALID_LEASE]")
    def active(self, now:datetime)->bool:
        if now.tzinfo is None: raise ValueError("REFUSED[NAIVE_NOW]")
        return self.issued_at <= now < self.expires_at
