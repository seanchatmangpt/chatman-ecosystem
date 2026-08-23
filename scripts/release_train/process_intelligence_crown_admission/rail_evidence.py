from dataclasses import dataclass
from enum import Enum
from .identity import Subject
from .refusal import require

class Rail(str, Enum):
    SEMANTIC="SEMANTIC"; POWL="POWL"; REACTOR="REACTOR"; BEAM="BEAM"; PLAN="PLAN"
    WASM="WASM"; NIF="NIF"; REMOTE="REMOTE"; DISTRIBUTED="DISTRIBUTED"; REPLAY="REPLAY"; BRCE="BRCE"

class Outcome(str, Enum):
    PASS="PASS"; FAIL="FAIL"; PENDING="PENDING"; UNKNOWN="UNKNOWN"; UNSUPPORTED="UNSUPPORTED"

@dataclass(frozen=True)
class RailEvidence:
    subject: Subject
    rail: Rail
    source_id: str
    outcome: Outcome
    semantic_digest: str

    def __post_init__(self):
        require(bool(self.source_id.strip()), "EMPTY_EVIDENCE_SOURCE")
        require(self.semantic_digest == self.subject.semantic_digest, "FOREIGN_RAIL_DIGEST")

def reconcile(rows):
    by={}
    for row in rows:
        key=(row.rail,row.source_id)
        if key in by: require(by[key] == row, "CONTRADICTORY_RAIL_EVIDENCE", str(key))
        by[key]=row
    return tuple(sorted(by.values(), key=lambda r:(r.rail.value,r.source_id)))
