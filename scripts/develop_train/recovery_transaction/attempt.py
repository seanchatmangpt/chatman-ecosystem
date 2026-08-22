from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .context import RecoveryContext, digest_json
from .lease import Lease
from .subject import Refusal

@dataclass(frozen=True)
class RecoveryAttempt:
    consumer: str
    base_context: RecoveryContext
    target_context: RecoveryContext
    ordinal: int
    issued_at: datetime
    lease: Lease
    nonce: str
    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise Refusal("INVALID_RECOVERY_ORDINAL", "ordinal must be non-negative")
        if not self.consumer.strip() or not self.nonce.strip():
            raise Refusal("INVALID_RECOVERY_ATTEMPT", "consumer and nonce required")
        if self.base_context.subject != self.target_context.subject:
            raise Refusal("CROSS_SUBJECT_RECOVERY", "base/target subject mismatch")
    @property
    def attempt_id(self) -> str:
        return digest_json({"consumer": self.consumer, "base": self.base_context.digest, "target": self.target_context.digest, "ordinal": self.ordinal, "issued_at": self.issued_at.isoformat(), "nonce": self.nonce})
