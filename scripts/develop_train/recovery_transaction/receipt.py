from __future__ import annotations
from dataclasses import dataclass
from .context import digest_json

SCHEMA = "chatman.develop-recovery-transaction/1"

@dataclass(frozen=True)
class QualificationReceipt:
    consumer: str
    attempt_id: str
    current_context_digest: str
    strategy: str
    standing: str
    blockers: tuple[str, ...]
    store: str
    actuation_performed: bool = False
    parent_digest: str | None = None
    def payload(self) -> dict:
        return {"schema": SCHEMA, "consumer": self.consumer, "attempt_id": self.attempt_id, "current_context_digest": self.current_context_digest, "strategy": self.strategy, "standing": self.standing, "blockers": list(self.blockers), "store": self.store, "actuation_performed": self.actuation_performed, "parent_digest": self.parent_digest}
    @property
    def digest(self) -> str:
        return digest_json(self.payload())

def replay(receipt: QualificationReceipt, expected_digest: str) -> bool:
    return not receipt.actuation_performed and receipt.digest == expected_digest
