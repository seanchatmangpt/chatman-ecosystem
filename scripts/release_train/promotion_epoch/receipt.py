from dataclasses import dataclass
import hashlib, json
@dataclass(frozen=True)
class Receipt:
    schema:str
    predecessor:str
    subject:str
    selected:tuple
    barrier:str
    actuation_performed:bool
    digest:str
def _canon(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"))
def manufacture(predecessor, subject, selected, barrier):
    body={"schema":"chatman.promotion-epoch/1","predecessor":predecessor,"subject":subject,"selected":tuple(selected),"barrier":barrier,"actuation_performed":False}
    digest=hashlib.sha256(_canon(body).encode()).hexdigest()
    return Receipt(**body,digest=digest)
def replay(r):
    if r.actuation_performed: return False
    expected=manufacture(r.predecessor,r.subject,r.selected,r.barrier)
    return expected == r
