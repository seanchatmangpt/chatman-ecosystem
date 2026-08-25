import hashlib,json
from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Receipt:
    subject:str; semantic_digest:str; trace_digest:str; generation:int; standing:str; actuation_performed:bool=False
    @property
    def body(self): return {"schema":"chatman.develop-process-trace-correspondence/1","subject":self.subject,"semantic_digest":self.semantic_digest,"trace_digest":self.trace_digest,"generation":self.generation,"standing":self.standing,"actuation_performed":self.actuation_performed}
    @property
    def digest(self): return hashlib.sha256(json.dumps(self.body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def replay(r:Receipt,body,digest):
    if body!=r.body or digest!=r.digest: raise Refused("REPLAY_MISMATCH")
    if body.get("actuation_performed"): raise Refused("REPORTED_ACTUATION")
    return True
