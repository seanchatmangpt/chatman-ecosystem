from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

RAILS=frozenset({"SEMANTIC","POWL","REACTOR","PROJECTION","DISTRIBUTED","REPLAY","BRCE"})
STATES=frozenset({"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"})

@dataclass(frozen=True, order=True)
class RailEvidence:
    subject: Subject
    rail: str
    engine: str
    semantic_digest: str
    outcome: str
    evidence_id: str
    observed_at: datetime
    def __post_init__(self):
        if self.rail not in RAILS: raise Refused("REFUSED[UNKNOWN_RAIL]")
        if self.outcome not in STATES: raise Refused("REFUSED[INVALID_RAIL_OUTCOME]")
        if len(self.semantic_digest)!=64 or any(c not in "0123456789abcdef" for c in self.semantic_digest): raise Refused("REFUSED[INVALID_SEMANTIC_DIGEST]")
        if not self.engine or not self.evidence_id: raise Refused("REFUSED[EMPTY_EVIDENCE_IDENTITY]")
        if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_EVIDENCE_TIME]")
