from dataclasses import dataclass
import hashlib,json
from .errors import Refused
def canonical(body): return json.dumps(body,sort_keys=True,separators=(",",":"))
@dataclass(frozen=True)
class Receipt:
    body:dict; digest:str
    @classmethod
    def make(cls,body):
        if body.get("actuation_performed") is not False: raise Refused("RECEIPT_ACTUATION_FORBIDDEN")
        return cls(body,hashlib.sha256(canonical(body).encode()).hexdigest())
def replay(r):
    if hashlib.sha256(canonical(r.body).encode()).hexdigest()!=r.digest: raise Refused("RECEIPT_MISMATCH")
    if r.body.get("actuation_performed") is not False: raise Refused("RECEIPT_ACTUATION_FORBIDDEN")
    return "REPLAY_MATCH"
