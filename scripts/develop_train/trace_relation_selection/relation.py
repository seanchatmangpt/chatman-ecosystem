from enum import Enum

class Relation(str, Enum):
    ACTIVITY = "ACTIVITY"
    STUTTER = "STUTTER"
    PARTIAL_ORDER = "PARTIAL_ORDER"
    EXACT = "EXACT"

_STRONGER = {
    Relation.EXACT: {Relation.ACTIVITY, Relation.STUTTER, Relation.PARTIAL_ORDER},
    Relation.STUTTER: {Relation.ACTIVITY},
    Relation.PARTIAL_ORDER: {Relation.ACTIVITY},
    Relation.ACTIVITY: set(),
}

def stronger_than(left: Relation, right: Relation) -> bool:
    return right in _STRONGER[left]

def maximal(relations):
    items = tuple(dict.fromkeys(relations))
    return tuple(sorted(
        (r for r in items if not any(stronger_than(other, r) for other in items if other != r)),
        key=lambda r: r.value,
    ))
