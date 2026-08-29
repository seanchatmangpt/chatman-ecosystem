from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .refusal import Refused

@dataclass(frozen=True)
class Receipt:
    subject_key: str
    trace_digest: str
    standing: str
    parents: tuple[str, ...] = ()
    authority: str = "SELECT"
    actuation_performed: bool = False

    def body(self) -> dict:
        return {"subject_key": self.subject_key, "trace_digest": self.trace_digest, "standing": self.standing, "parents": sorted(self.parents), "authority": self.authority, "actuation_performed": self.actuation_performed}

    @property
    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.body(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def replay(receipt: Receipt, expected_digest: str) -> None:
    if receipt.actuation_performed:
        raise Refused("RECEIPT_REPORTS_AMBIENT_ACTUATION")
    if receipt.digest != expected_digest:
        raise Refused("RECEIPT_MISMATCH")
