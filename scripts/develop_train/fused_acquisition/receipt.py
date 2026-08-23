from dataclasses import dataclass
import hashlib,json
from .refusals import Refused

@dataclass(frozen=True)
class Receipt:
    subject:str
    frontier_generation:int
    topology:str
    strategy:str
    selected_candidate:str|None
    standing:str
    actuation_performed:bool=False
    def body(self):
        return {"schema":"chatman.develop-fused-acquisition/1","subject":self.subject,"frontier_generation":self.frontier_generation,"topology":self.topology,"strategy":self.strategy,"selected_candidate":self.selected_candidate,"standing":self.standing,"actuation_performed":self.actuation_performed}
    def digest(self):
        return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()).hexdigest()

def replay(receipt:Receipt, expected_digest:str)->bool:
    if receipt.actuation_performed: raise Refused("REPORTED_ACTUATION")
    if receipt.digest()!=expected_digest: raise Refused("RECEIPT_MISMATCH")
    return True
