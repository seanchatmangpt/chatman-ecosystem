from dataclasses import dataclass
import hashlib, json
from .errors import Refused

def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",",":"))

@dataclass(frozen=True)
class Receipt:
    subject: str
    generation: int
    standing: str
    calibration_digest: str
    authority: str = "SELECT"
    actuation_performed: bool = False

    def __post_init__(self):
        if self.authority not in {"OBSERVE","SELECT","CONSTRUCT","VERIFY"}:
            raise Refused("INVALID_RECEIPT_AUTHORITY")
        if self.actuation_performed:
            raise Refused("REPORTED_AMBIENT_ACTUATION")

    @property
    def body(self):
        return {"schema":"chatman.develop-certificate-federation-realization-control/1","subject":self.subject,"generation":self.generation,"standing":self.standing,"calibration_digest":self.calibration_digest,"authority":self.authority,"actuation_performed":self.actuation_performed}

    @property
    def digest(self):
        return hashlib.sha256(_canon(self.body).encode()).hexdigest()

def replay(receipt: Receipt, expected_digest: str):
    if receipt.digest != expected_digest:
        raise Refused("RECEIPT_DIGEST_MISMATCH")
    return "REPLAY_MATCH"
