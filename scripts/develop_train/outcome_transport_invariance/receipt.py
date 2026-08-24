from dataclasses import dataclass
import hashlib
import json
from .errors import Refused

def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

@dataclass(frozen=True)
class Receipt:
    subject: str
    strategy: str
    standing: str
    evidence: str
    authority: str = "SELECT"
    actuation_performed: bool = False

    @property
    def body(self):
        if self.actuation_performed:
            raise Refused("REPORTED_AMBIENT_ACTUATION")
        if self.authority not in {"OBSERVE", "SELECT", "CONSTRUCT", "VERIFY"}:
            raise Refused("INVALID_RECEIPT_AUTHORITY")
        return {"schema": "chatman.develop-outcome-transport-invariance/1", "subject": self.subject, "strategy": self.strategy, "standing": self.standing, "evidence": self.evidence, "authority": self.authority, "actuation_performed": False}

    @property
    def digest(self):
        return hashlib.sha256(canon(self.body).encode()).hexdigest()

def replay(receipt, expected):
    if receipt.digest != expected:
        raise Refused("RECEIPT_DIGEST_MISMATCH")
    return "REPLAY_MATCH"
