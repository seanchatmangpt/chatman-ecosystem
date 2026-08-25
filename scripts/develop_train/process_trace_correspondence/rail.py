from enum import Enum
from dataclasses import dataclass
from .errors import Refused
class Rail(str,Enum):
    METHODOLOGY="METHODOLOGY"; POWL="POWL"; REACTOR="REACTOR"; PROJECTION="PROJECTION"; DISTRIBUTED="DISTRIBUTED"; REPLAY="REPLAY"; BRCE="BRCE"; ORACLE="ORACLE"; CI="CI"
@dataclass(frozen=True)
class RailEvidence:
    rail:Rail; subject:str; semantic_digest:str; trace_digest:str; generation:int
def index(evidence):
    out={}
    for e in evidence:
        if e.rail in out: raise Refused("DUPLICATE_RAIL")
        out[e.rail]=e
    return out
