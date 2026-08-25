from dataclasses import dataclass
from .subject import Subject,Refused
KINDS={"METHODOLOGY","POWL","REACTOR","PROJECTION","DISTRIBUTED","REPLAY","BRCE","ORACLE","CI"}
@dataclass(frozen=True,order=True)
class RailEvidence:
    subject:Subject; rail_id:str; kind:str; semantic_digest:str; trace_digest:str; state:str
    def __post_init__(self):
        if self.kind not in KINDS: raise Refused("REFUSED[UNKNOWN_RAIL_KIND]")
        for x in (self.semantic_digest,self.trace_digest):
            if len(x)!=64 or any(c not in "0123456789abcdef" for c in x): raise Refused("REFUSED[INVALID_DIGEST]")
        if self.state not in {"PASS","FAIL","UNKNOWN","UNSUPPORTED","REFUSED"}: raise Refused("REFUSED[INVALID_RAIL_STATE]")
