from dataclasses import dataclass
import hashlib,json
from .errors import Refused
@dataclass(frozen=True)
class Receipt:
    subject: str
    generation: int
    strategy: str
    composition_mode: str
    standing: str
    evidence_ids: tuple[str,...]
    replay_root: str
    authority: str="SELECT"
    actuation_performed: bool=False
    @property
    def body(self):
        if self.actuation_performed: raise Refused("REPORTED_AMBIENT_ACTUATION")
        return {"schema":"chatman.develop-validation-independence/1","subject":self.subject,"generation":self.generation,"strategy":self.strategy,"composition_mode":self.composition_mode,"standing":self.standing,"evidence_ids":sorted(self.evidence_ids),"replay_root":self.replay_root,"authority":self.authority,"actuation_performed":False}
    @property
    def digest(self):
        raw=json.dumps(self.body,sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()
def replay(receipt,digest):
    if receipt.digest!=digest: raise Refused("RECEIPT_DRIFT")
    return "REPLAY_MATCH"
