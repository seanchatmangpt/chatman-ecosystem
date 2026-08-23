from enum import Enum
from .subject import Refused

class Relation(str, Enum):
    ACTIVITY="ACTIVITY"
    STUTTER="STUTTER"
    PARTIAL_ORDER="PARTIAL_ORDER"
    EXACT="EXACT"

_DOMINATES={
    Relation.EXACT:{Relation.STUTTER,Relation.PARTIAL_ORDER,Relation.ACTIVITY},
    Relation.STUTTER:{Relation.ACTIVITY},
    Relation.PARTIAL_ORDER:{Relation.ACTIVITY},
    Relation.ACTIVITY:set(),
}

def stronger_than(left, right):
    return right in _DOMINATES[left]

def comparable(left, right):
    return left==right or stronger_than(left,right) or stronger_than(right,left)

def require_noncollapsed():
    if comparable(Relation.STUTTER, Relation.PARTIAL_ORDER):
        raise Refused("REFUSED[RELATION_LATTICE_COLLAPSED]")
    return True
