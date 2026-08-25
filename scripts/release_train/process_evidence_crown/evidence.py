from dataclasses import dataclass
from enum import Enum
from .interval import Interval
from .subject import Subject
from .refusal import Refused

class EvidenceKind(str, Enum):
    SEMANTIC='SEMANTIC'; TRACE='TRACE'; CALIBRATION='CALIBRATION'; REALIZATION='REALIZATION'; METHODOLOGY='METHODOLOGY'; RUNTIME='RUNTIME'; SECURITY='SECURITY'; FAILURE='FAILURE'; AUTHORITY='AUTHORITY'; REPLAY='REPLAY'; ORACLE='ORACLE'
class Outcome(str, Enum): PASS='PASS'; FAIL='FAIL'; UNKNOWN='UNKNOWN'; UNSUPPORTED='UNSUPPORTED'

@dataclass(frozen=True)
class EvidenceNode:
    id: str; subject: Subject; kind: EvidenceKind; generation: int; confidence: Interval; outcome: Outcome
    implementation: str; model: str; domain: str; cost: int=1
    def __post_init__(self):
        if not self.id or self.generation < 0 or self.cost < 0: raise Refused("INVALID_EVIDENCE_NODE", self.id)
        if not self.implementation or not self.model or not self.domain: raise Refused("MISSING_PROVENANCE", self.id)
