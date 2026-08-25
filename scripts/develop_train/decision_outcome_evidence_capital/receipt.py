from dataclasses import dataclass
import hashlib, json
from .errors import Refused

def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",",":"))

@dataclass(frozen=True)
class Receipt:
    subject: str
    policy_generation: int
    standing: str
    evidence_digest: str
    authority: str = "SELECT"
    actuation_performed: bool = False

    def __post_init__(self):
        if self.actuation_performed:
            raise Refused("REPORTED_AMBIENT_ACTUATION")
        if self.authority not in {"OBSERVE","SELECT","CONSTRUCT","VERIFY"}:
            raise Refused("INVALID_RECEIPT_AUTHORITY")

    @property
    def body(self):
        return {
            "schema":"chatman.develop-decision-outcome-evidence-capital/1",
            "subject":self.subject,
            "policy_generation":self.policy_generation,
            "standing":self.standing,
            "evidence_digest":self.evidence_digest,
            "authority":self.authority,
            "actuation_performed":self.actuation_performed,
        }

    @property
    def digest(self):
        return hashlib.sha256(_canon(self.body).encode()).hexdigest()

def replay(receipt: Receipt, expected_digest: str):
    if receipt.digest != expected_digest:
        raise Refused("RECEIPT_DIGEST_MISMATCH")
    if receipt.actuation_performed:
        raise Refused("REPORTED_AMBIENT_ACTUATION")
    return "REPLAY_MATCH"
