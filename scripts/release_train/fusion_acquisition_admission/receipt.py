from dataclasses import dataclass,replace
import hashlib,json
from .errors import Refused

SCHEMA="chatman.fusion-acquisition-admission/1"

@dataclass(frozen=True)
class Receipt:
    subject:str
    calibration_generation:int
    topology:str
    standing:str
    blockers:tuple[str,...]
    selected_acquisition:str|None
    strategy:str|None
    authority:str="SELECT"
    phases:tuple[str,...]=("VERIFY","CONSTRUCT")
    actuation_performed:bool=False
    digest:str=""
    def body(self):
        return {"schema":SCHEMA,"subject":self.subject,"calibration_generation":self.calibration_generation,"topology":self.topology,"standing":self.standing,"blockers":list(self.blockers),"selected_acquisition":self.selected_acquisition,"strategy":self.strategy,"authority":self.authority,"phases":list(self.phases),"actuation_performed":self.actuation_performed}
    def seal(self):
        raw=json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()
        return replace(self,digest=hashlib.sha256(raw).hexdigest())
    def replay(self):
        if self.authority!="SELECT" or self.phases!=("VERIFY","CONSTRUCT") or self.actuation_performed: raise Refused("RECEIPT_AUTHORITY_DRIFT")
        if self.digest!=self.seal().digest: raise Refused("RECEIPT_TAMPER")
        return True
