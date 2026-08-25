from enum import Enum
from .subject import Refused

class Relation(str, Enum):
    EXACT="EXACT"
    STUTTER="STUTTER"
    ACTIVITY="ACTIVITY"
    PARTIAL_ORDER="PARTIAL_ORDER"

IMPLIES = {
    Relation.EXACT: frozenset(Relation),
    Relation.STUTTER: frozenset({Relation.STUTTER, Relation.ACTIVITY}),
    Relation.PARTIAL_ORDER: frozenset({Relation.PARTIAL_ORDER, Relation.ACTIVITY}),
    Relation.ACTIVITY: frozenset({Relation.ACTIVITY}),
}

def require_noncollapsed(observed: dict[Relation,bool]):
    if set(observed) != set(Relation):
        raise Refused("REFUSED[INCOMPLETE_RELATION_LATTICE]")
    if observed[Relation.EXACT] and not all(observed[r] for r in IMPLIES[Relation.EXACT]):
        raise Refused("REFUSED[RELATION_IMPLICATION_VIOLATION]")
    return True
