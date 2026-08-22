from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
SCHEMA="chatman.develop-selection-intent/1"
@dataclass(frozen=True,slots=True)
class QualificationReceipt:
    consumer:str; selected_cut_id:str; recovery_strategy:str; policy_digest:str; frontier_digest:str; standing:str; store:str; actuation_performed:bool=False
    def body(self)->dict:
        return {"schema":SCHEMA,"consumer":self.consumer,"selected_cut_id":self.selected_cut_id,"recovery_strategy":self.recovery_strategy,"policy_digest":self.policy_digest,"frontier_digest":self.frontier_digest,"standing":self.standing,"store":self.store,"actuation_performed":self.actuation_performed}
    @property
    def digest(self)->str: return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def replay(receipt:QualificationReceipt,expected_digest:str)->bool: return not receipt.actuation_performed and receipt.digest==expected_digest
