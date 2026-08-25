import hashlib, json
from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str; generation: int; standing: str; evidence_digest: str; transport_digest: str; authority: str="SELECT"; actuation_performed: bool=False
    def body(self):
        return {"schema":"chatman.outcome-capital-transport/1","subject":self.subject,"generation":self.generation,"standing":self.standing,"evidence_digest":self.evidence_digest,"transport_digest":self.transport_digest,"authority":self.authority,"actuation_performed":self.actuation_performed}
    def digest(self): return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def replay(receipt,digest):
    if receipt.actuation_performed: raise Refused("REPORTED_AMBIENT_ACTUATION")
    if receipt.digest()!=digest: raise Refused("RECEIPT_TAMPER")
    return "REPLAY_MATCH"
