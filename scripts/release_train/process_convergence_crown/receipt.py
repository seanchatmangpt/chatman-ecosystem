from dataclasses import dataclass
import hashlib, json
from .refusal import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str
    generation: int
    strategy: str
    standing: str
    actuation_performed: bool=False
    def body(self):
        return {"subject":self.subject,"generation":self.generation,"strategy":self.strategy,"standing":self.standing,"actuation_performed":self.actuation_performed}
    def digest(self):
        if self.actuation_performed: raise Refused("RECEIPT_REPORTS_ACTUATION")
        raw=json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()

def replay(receipt: Receipt, expected: str):
    if receipt.digest()!=expected: raise Refused("RECEIPT_MISMATCH")
    return "REPLAY_MATCH"
