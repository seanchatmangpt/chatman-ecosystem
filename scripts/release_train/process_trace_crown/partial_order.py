from __future__ import annotations
from .independence import Independence
from .trace import Trace

def signature(trace: Trace, independence: Independence) -> frozenset[tuple[tuple[str,str,str], tuple[str,str,str]]]:
    edges = set()
    events = trace.events
    for i, left in enumerate(events):
        for right in events[i+1:]:
            if not independence.independent(left, right):
                a = (left.activity, left.object_id, left.lifecycle)
                b = (right.activity, right.object_id, right.lifecycle)
                edges.add((a, b))
    return frozenset(edges)

def equivalent(left: Trace, right: Trace, independence: Independence) -> bool:
    left_events = sorted((e.activity, e.object_id, e.lifecycle) for e in left.events)
    right_events = sorted((e.activity, e.object_id, e.lifecycle) for e in right.events)
    return left.subject == right.subject and left_events == right_events and signature(left, independence) == signature(right, independence)
