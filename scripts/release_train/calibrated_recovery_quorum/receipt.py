from dataclasses import dataclass
from hashlib import sha256
import json
from .subject import Refused
SCHEMA="chatman.calibrated-recovery-quorum/1"
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"))
@dataclass(frozen=True)
class Receipt:
    payload: dict; digest: str
    @classmethod
    def manufacture(cls,payload):
        body={"schema":SCHEMA,**payload,"actuation_performed":False}
        return cls(body,sha256(canonical(body).encode()).hexdigest())
    def replay(self):
        if self.payload.get("schema")!=SCHEMA or self.payload.get("actuation_performed") is not False: raise Refused("REFUSED[RECEIPT_AUTHORITY_DRIFT]")
        expected=sha256(canonical(self.payload).encode()).hexdigest()
        if expected!=self.digest: raise Refused("REFUSED[RECEIPT_MISMATCH]")
        return True
