from dataclasses import dataclass
import hashlib, json
from .refusal import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str
    generation: int
    strategy: str
    direction: str
    standing: str
    actuation_performed: bool=False

    def __post_init__(self):
        if self.actuation_performed:
            raise Refused("REPORTED_AMBIENT_ACTUATION")

    def body(self):
        return {"schema":"chatman.develop-process-convergence/1","subject":self.subject,"generation":self.generation,"strategy":self.strategy,"direction":self.direction,"standing":self.standing,"actuation_performed":False}

    def digest(self):
        raw=json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()


def replay(receipt: Receipt, expected_digest: str) -> bool:
    if receipt.actuation_performed:
        raise Refused("REPORTED_AMBIENT_ACTUATION")
    if receipt.digest() != expected_digest:
        raise Refused("RECEIPT_DIGEST_MISMATCH")
    return True
