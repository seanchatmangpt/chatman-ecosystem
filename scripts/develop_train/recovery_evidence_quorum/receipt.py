from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .policy import Standing

SCHEMA = "chatman.develop-recovery-evidence-quorum/1"


@dataclass(frozen=True, slots=True)
class QualificationReceipt:
    subject: str
    attempt_id: str
    standing: Standing
    clusters: tuple[tuple[str, ...], ...]
    diversity: str
    blockers: tuple[str, ...]
    store: str
    action: str
    actuation_performed: bool = False
    schema: str = SCHEMA

    def body(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "subject": self.subject,
            "attempt_id": self.attempt_id,
            "standing": self.standing.value,
            "clusters": [list(x) for x in self.clusters],
            "diversity": self.diversity,
            "blockers": list(self.blockers),
            "store": self.store,
            "action": self.action,
            "actuation_performed": self.actuation_performed,
        }

    @property
    def digest(self) -> str:
        payload = json.dumps(self.body(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()


def replay(receipt: QualificationReceipt, expected_digest: str) -> bool:
    return receipt.schema == SCHEMA and not receipt.actuation_performed and receipt.digest == expected_digest
