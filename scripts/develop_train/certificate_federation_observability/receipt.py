from dataclasses import dataclass
import hashlib,json
from .errors import Refused
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
@dataclass(frozen=True)
class Receipt:
    subject:str; generation:int; standing:str; quorum_digest:str; authority:str="VERIFY"; actuation_performed:bool=False
    def __post_init__(self):
        if self.authority not in {"OBSERVE","SELECT","CONSTRUCT","VERIFY"}: raise Refused("INVALID_RECEIPT_AUTHORITY")
        if self.actuation_performed: raise Refused("REPORTED_AMBIENT_ACTUATION")
    @property
    def body(self): return {"schema":"chatman.develop-certificate-federation-observability/1","subject":self.subject,"generation":self.generation,"standing":self.standing,"quorum_digest":self.quorum_digest,"authority":self.authority,"actuation_performed":self.actuation_performed}
    @property
    def digest(self): return hashlib.sha256(canon(self.body).encode()).hexdigest()
