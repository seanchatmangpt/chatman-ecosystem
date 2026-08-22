from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .subject import Refusal
SCHEMA="chatman.recovery-transaction/1"
def canonical(body:dict)->bytes:return json.dumps(body,sort_keys=True,separators=(",",":")).encode()
@dataclass(frozen=True)
class Receipt:
    body: dict
    digest: str
    @classmethod
    def make(cls,body:dict)->"Receipt":
        bounded={"schema":SCHEMA,**body,"actuation_performed":False}
        return cls(bounded,hashlib.sha256(canonical(bounded)).hexdigest())
    def replay(self)->bool:
        if self.body.get("schema")!=SCHEMA or self.body.get("actuation_performed") is not False:return False
        return hashlib.sha256(canonical(self.body)).hexdigest()==self.digest
    def require_replay(self)->None:
        if not self.replay():raise Refusal("REFUSED[RECOVERY_RECEIPT_REPLAY_MISMATCH]")
