from dataclasses import dataclass
import hashlib,json
from .errors import Refused

def _canon(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"))
@dataclass(frozen=True)
class Receipt:
    subject:str
    strategy:str
    standing:str
    evidence_digest:str
    authority:str="SELECT"
    actuation_performed:bool=False
    @property
    def body(self):
        if self.actuation_performed:
            raise Refused("REPORTED_ACTUATION")
        if self.authority!="SELECT":
            raise Refused("INVALID_RECEIPT_AUTHORITY")
        return {"schema":"chatman.develop-distributional-process-capital/1","subject":self.subject,"strategy":self.strategy,"standing":self.standing,"evidence_digest":self.evidence_digest,"authority":self.authority,"actuation_performed":False}
    @property
    def digest(self):
        return hashlib.sha256(_canon(self.body).encode()).hexdigest()
def replay(receipt,expected):
    if receipt.digest!=expected:
        raise Refused("RECEIPT_TAMPER")
    _=receipt.body
    return "REPLAY_MATCH"
