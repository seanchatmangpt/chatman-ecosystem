from __future__ import annotations
from .trace import Trace

def activity_projection(trace: Trace) -> tuple[tuple[str, str], ...]:
    return tuple(event.activity_key for event in trace.events)

def stutter_reduction(trace: Trace) -> tuple[tuple[str, str], ...]:
    out: list[tuple[str, str]] = []
    for key in activity_projection(trace):
        if not out or out[-1] != key:
            out.append(key)
    return tuple(out)
