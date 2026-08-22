from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

_SCHEMA = "chatman.develop-calibrated-recovery-quorum/1"


@dataclass(frozen=True, slots=True)
class QualificationReceipt:
    subject: str
    attempt_id: str
    calibrated_sources: tuple[str, ...]
    independent_clusters: int
    statistic: str
    decision: str
    blockers: tuple[str, ...]
    store: str
    standing: str
    actuation_performed: bool = False
    schema: str = _SCHEMA

    def payload(self) -> dict[str, object]:
        return asdict(self)

    def digest(self) -> str:
        body = json.dumps(self.payload(), sort_keys=True, separators=(",", ":"))
        return sha256(body.encode()).hexdigest()


def replay(receipt: QualificationReceipt, expected_digest: str) -> bool:
    return (
        receipt.schema == _SCHEMA
        and not receipt.actuation_performed
        and receipt.digest() == expected_digest
    )
