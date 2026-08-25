from dataclasses import dataclass
from enum import Enum
from .relation import Relation,discharges
from .refusal import Refused
class Rail(str,Enum):
    METHODOLOGY="METHODOLOGY"; POWL="POWL"; REACTOR="REACTOR"; PROJECTION="PROJECTION"; DISTRIBUTED="DISTRIBUTED"; REPLAY="REPLAY"; BRCE="BRCE"; ORACLE="ORACLE"; CI="CI"
@dataclass(frozen=True)
class RailEvidence:
    rail:Rail; subject:str; relation:Relation; status:str
def require_rails(rows,subject,required_relation):
    if {r.rail for r in rows}!=set(Rail): raise Refused("INCOMPLETE_RAIL_SET")
    for r in rows:
        if r.subject!=subject: raise Refused("FOREIGN_RAIL_SUBJECT")
        if r.status!="PASS": raise Refused("RAIL_FAILURE")
        if not discharges(r.relation,required_relation): raise Refused("RELATION_TOO_WEAK")
    return True
