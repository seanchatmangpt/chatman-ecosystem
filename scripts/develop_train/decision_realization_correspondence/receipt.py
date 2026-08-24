import hashlib
import json
from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str
    policy_generation: int
    standing: str
    realization_digest: str
    authority: str = "SELECT"
    actuation_performed: bool = False

    def body(self):
        if self.actuation_performed:
            raise Refused("REPORTED_AMBIENT_ACTUATION")
        return {
            "schema": "chatman.develop-decision-realization-correspondence/1",
            "subject": self.subject,
            "policy_generation": self.policy_generation,
            "standing": self.standing,
            "realization_digest": self.realization_digest,
            "authority": self.authority,
            "actuation_performed": False,
        }

    def digest(self):
        raw=json.dumps(self.body(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

def replay(receipt: Receipt, expected_digest: str):
    if receipt.actuation_performed or receipt.authority != "SELECT":
        raise Refused("INVALID_RECEIPT_AUTHORITY")
    if receipt.digest() != expected_digest:
        raise Refused("RECEIPT_DIGEST_MISMATCH")
    return "REPLAY_MATCH"
