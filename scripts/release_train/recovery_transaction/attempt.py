from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import hashlib, json
from .lease import Lease
from .subject import Subject, Refusal
@dataclass(frozen=True)
class RecoveryAttempt:
    consumer: Subject
    before_digest: str
    target_digest: str
    ordinal: int
    nonce: str
    issued_at: datetime
    lease: Lease
    def __post_init__(self) -> None:
        if self.ordinal < 0 or not self.nonce or self.issued_at.tzinfo is None or not self.lease.active(self.issued_at):
            raise Refusal("REFUSED[INVALID_RECOVERY_ATTEMPT]")
    @property
    def attempt_id(self) -> str:
        body={"consumer":self.consumer.exact_id,"before":self.before_digest,"target":self.target_digest,"ordinal":self.ordinal,"nonce":self.nonce,"issued_at":self.issued_at.isoformat()}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
