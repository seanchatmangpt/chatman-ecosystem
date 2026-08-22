from dataclasses import dataclass
from datetime import datetime
from .subject import Refused

@dataclass(frozen=True, order=True)
class EvidenceLease:
    bound_receipt_sha256: str
    issued_at: datetime
    expires_at: datetime

    def __post_init__(self):
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise Refused("REFUSED[NAIVE_LEASE_TIME]")
        if self.expires_at <= self.issued_at:
            raise Refused("REFUSED[INVALID_LEASE_INTERVAL]")
        if len(self.bound_receipt_sha256) != 64:
            raise Refused("REFUSED[INVALID_LEASE_RECEIPT]")
