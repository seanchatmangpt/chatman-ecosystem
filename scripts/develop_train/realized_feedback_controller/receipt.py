from dataclasses import dataclass
import hashlib, json
from .errors import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str
    policy_generation: int
    feedback: str
    standing: str
    actuation_performed: bool=False

    def __post_init__(self):
        if self.actuation_performed:
            raise Refused("REFUSED_RECEIPT_REPORTS_ACTUATION")

    def body(self):
        return {"actuation_performed":False,"feedback":self.feedback,"policy_generation":self.policy_generation,"standing":self.standing,"subject":self.subject}

    def digest(self):
        raw=json.dumps(self.body(),sort_keys=True,separators=(",",":"))
        return hashlib.sha256(raw.encode()).hexdigest()

def replay(receipt: Receipt, digest: str):
    return receipt.digest()==digest and receipt.actuation_performed is False
