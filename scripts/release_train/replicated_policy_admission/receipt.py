from dataclasses import dataclass,asdict
from hashlib import sha256
import json
from .refusal import Refused
SCHEMA="chatman.replicated-policy-admission/1"
@dataclass(frozen=True)
class Receipt:
    subject:str; generation:int; policy_digest:str|None; frontier_digest:str|None; replicas:tuple[str,...]; blockers:tuple[str,...]; standing:str; reason:str
    phases:tuple[str,...]=("VERIFY","CONSTRUCT"); authority:str="SELECT"; actuation_performed:bool=False
    @property
    def body(self)->dict: return {"schema":SCHEMA,**asdict(self)}
    @property
    def digest(self)->str: return sha256(json.dumps(self.body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def replay(receipt:Receipt,digest:str)->bool:
    if receipt.actuation_performed: raise Refused("REPORTED_ACTUATION")
    if receipt.authority!="SELECT" or receipt.phases!=("VERIFY","CONSTRUCT"): raise Refused("AUTHORITY_DRIFT")
    return receipt.digest==digest
