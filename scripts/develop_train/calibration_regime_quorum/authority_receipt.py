from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .subject import Refusal,Subject
class ActionClass:
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def require_action(action:str)->None:
    if action==ActionClass.DO: raise Refusal("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
    if action not in {ActionClass.OBSERVE,ActionClass.SELECT,ActionClass.CONSTRUCT,ActionClass.VERIFY}: raise Refusal("REFUSED[UNKNOWN_ACTION_CLASS]")
@dataclass(frozen=True,slots=True)
class QualificationReceipt:
    subject:Subject; regime_generations:tuple[tuple[str,int],...]; decision:str; standing:str; store:str; blockers:tuple[str,...]; actuation_performed:bool=False; schema:str="chatman.develop-calibration-regime-quorum/1"
    def body(self)->dict[str,object]:
        return {"actuation_performed":self.actuation_performed,"blockers":list(self.blockers),"decision":self.decision,"regime_generations":[list(x) for x in self.regime_generations],"schema":self.schema,"standing":self.standing,"store":self.store,"subject":self.subject.exact_id}
    def digest(self)->str:
        return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def replay(receipt:QualificationReceipt,expected_digest:str)->bool:
    return (not receipt.actuation_performed) and receipt.digest()==expected_digest
