from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
from .interval import Interval
@dataclass(frozen=True, order=True)
class EvidenceNode:
    subject: Subject
    evidence_id: str
    kind: str
    generation: int
    interval: Interval
    implementation_digest: str
    model_digest: str
    domain: str
    observed_at: datetime
    state: str = "PASS"
    def __post_init__(self):
        if not self.evidence_id or self.generation < 0:
            raise Refused("REFUSED[INVALID_EVIDENCE_IDENTITY]")
        if len(self.implementation_digest)!=64 or len(self.model_digest)!=64:
            raise Refused("REFUSED[INVALID_PROVENANCE_DIGEST]")
        if self.observed_at.tzinfo is None:
            raise Refused("REFUSED[NAIVE_EVIDENCE_TIME]")
        if self.state not in {"PASS","FAIL","UNKNOWN","UNSUPPORTED","REFUSED"}:
            raise Refused("REFUSED[INVALID_EVIDENCE_STATE]")
