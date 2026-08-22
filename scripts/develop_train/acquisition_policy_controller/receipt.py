from dataclasses import dataclass,asdict,replace
from hashlib import sha256
import json
SCHEMA="chatman.develop-acquisition-policy-controller/1"
@dataclass(frozen=True, slots=True)
class Receipt:
    subject:str
    policy_generation:int
    policy_digest:str
    frontier_digest:str
    selected_strategy:str|None
    standing:str
    authority:str="SELECT"
    actuation_performed:bool=False
    parent:str|None=None
    digest:str=""
    def body(self): d=asdict(self); d.pop("digest"); return d
def issue(subject,**kwargs):
    r=Receipt(subject=subject.exact,**kwargs); dig=sha256(json.dumps({"schema":SCHEMA,**r.body()},sort_keys=True,separators=(",",":")).encode()).hexdigest(); return replace(r,digest=dig)
def replay(r):
    if r.actuation_performed or r.authority!="SELECT":return False
    e=sha256(json.dumps({"schema":SCHEMA,**r.body()},sort_keys=True,separators=(",",":")).encode()).hexdigest(); return e==r.digest
