from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .refusal import Refused
from .subject import Subject

class Rail(str, Enum):
    METHODOLOGY="METHODOLOGY"; POWL="POWL"; REACTOR="REACTOR"; PROJECTION="PROJECTION"; DISTRIBUTED="DISTRIBUTED"; REPLAY="REPLAY"; BRCE="BRCE"; ORACLE="ORACLE"; CI="CI"

@dataclass(frozen=True)
class RailEvidence:
    rail: Rail
    subject: Subject
    trace_digest: str
    state: str

def admit(rows: tuple[RailEvidence, ...]) -> None:
    if not rows:
        raise Refused("EMPTY_RAIL_EVIDENCE")
    if len({r.rail for r in rows}) != len(rows):
        raise Refused("DUPLICATE_RAIL_EVIDENCE")
    if len({r.subject for r in rows}) != 1:
        raise Refused("CROSS_RAIL_SUBJECT_DRIFT")
    passed = [r for r in rows if r.state == "PASS"]
    if len({r.trace_digest for r in passed}) > 1:
        raise Refused("CROSS_RAIL_TRACE_DIVERGENCE")
