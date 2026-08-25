from __future__ import annotations
from enum import Enum
from .normalize import activity_projection, stutter_reduction
from .trace import Trace

class Relation(str, Enum):
    EXACT = "EXACT"
    ACTIVITY = "ACTIVITY"
    STUTTER = "STUTTER"
    PARTIAL_ORDER = "PARTIAL_ORDER"

def exact(left: Trace, right: Trace) -> bool:
    return left.subject == right.subject and left.events == right.events

def activity(left: Trace, right: Trace) -> bool:
    return left.subject == right.subject and activity_projection(left) == activity_projection(right)

def stutter(left: Trace, right: Trace) -> bool:
    return left.subject == right.subject and stutter_reduction(left) == stutter_reduction(right)
