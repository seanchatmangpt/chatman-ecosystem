from enum import Enum
from .normalize import Profile,project
class Relation(str,Enum): EXACT="EXACT"; ACTIVITY="ACTIVITY"; STUTTER="STUTTER"; PARTIAL_ORDER="PARTIAL_ORDER"
STRENGTH={Relation.EXACT:4,Relation.ACTIVITY:3,Relation.STUTTER:2,Relation.PARTIAL_ORDER:1}
def equivalent(a,b,relation):
    r=Relation(relation)
    if r is Relation.PARTIAL_ORDER: raise ValueError("use partial_order.equivalent")
    return project(a,Profile(r.value))==project(b,Profile(r.value))
def discharges(proved,required): return STRENGTH[Relation(proved)]>=STRENGTH[Relation(required)]
