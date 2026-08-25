from __future__ import annotations
from enum import Enum

class Standing(str, Enum):
    UNKNOWN="UNKNOWN"; PARTIAL_ALIVE="PARTIAL_ALIVE"; ALIVE="ALIVE"; BLOCKED="BLOCKED"; BUILD_BROKEN="BUILD_BROKEN"

def compute(states: list[str], blockers: set[str], correspondence_ok: bool, complete: bool) -> Standing:
    if any(s == "FAIL" for s in states):
        return Standing.BUILD_BROKEN
    if blockers:
        return Standing.BLOCKED
    if not complete or not correspondence_ok or any(s in {"UNKNOWN","PENDING","UNSUPPORTED"} for s in states):
        return Standing.UNKNOWN
    return Standing.PARTIAL_ALIVE
