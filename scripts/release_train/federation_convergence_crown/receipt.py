import hashlib,json
from dataclasses import dataclass
@dataclass(frozen=True)
class Receipt:
    subject:str; standing:str; evidence_digest:str; authority:str="SELECT"; actuation_performed:bool=False
    def body(self):
        return {"subject":self.subject,"standing":self.standing,"evidence_digest":self.evidence_digest,"authority":self.authority,"actuation_performed":self.actuation_performed}
    def digest(self):
        return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()).hexdigest()
