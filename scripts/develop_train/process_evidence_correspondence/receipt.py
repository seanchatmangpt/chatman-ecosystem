import hashlib,json
from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Receipt:
    subject:str; generation:int; composition_mode:str; standing:str; replay_root:str; authority:str="SELECT"; actuation_performed:bool=False
    def body(self):
        return {"schema":"chatman.develop-process-evidence-correspondence/1","subject":self.subject,"generation":self.generation,"composition_mode":self.composition_mode,"standing":self.standing,"replay_root":self.replay_root,"authority":self.authority,"actuation_performed":self.actuation_performed}
    def digest(self):
        return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def replay(receipt,digest):
    if receipt.actuation_performed: raise Refused("REPORTED_AMBIENT_ACTUATION")
    if receipt.digest()!=digest: raise Refused("RECEIPT_DRIFT")
    return "REPLAY_MATCH"
