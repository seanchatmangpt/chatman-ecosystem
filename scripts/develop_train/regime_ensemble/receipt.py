from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from .subject import Subject

SCHEMA = "chatman.develop-detector-consensus/1"

@dataclass(frozen=True)
class QualificationReceipt:
    subject: str
    regime: str
    detectors: tuple[str, ...]
    standing: str
    actuation_performed: bool = False

    def body(self) -> dict[str, object]:
        return {"schema": SCHEMA, **asdict(self)}

    def digest(self) -> str:
        payload = json.dumps(self.body(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()

def issue(subject: Subject, regime: str, detectors: tuple[str, ...], standing: str) -> tuple[QualificationReceipt, str]:
    receipt = QualificationReceipt(subject.identity, regime, tuple(sorted(detectors)), standing, False)
    return receipt, receipt.digest()

def replay(receipt: QualificationReceipt, expected_digest: str) -> bool:
    return (not receipt.actuation_performed) and receipt.digest() == expected_digest
