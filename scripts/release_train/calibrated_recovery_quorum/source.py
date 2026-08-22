from dataclasses import dataclass
from hashlib import sha256
import json
from .subject import Refused

@dataclass(frozen=True)
class EvidenceSource:
    producer: str; run_id: str; artifact_id: str; family: str
    def __post_init__(self):
        if not all(str(x).strip() for x in (self.producer,self.run_id,self.artifact_id,self.family)):
            raise Refused("REFUSED[INCOMPLETE_EVIDENCE_SOURCE]")
    @property
    def fingerprint(self):
        body=[self.producer,self.run_id,self.artifact_id,self.family]
        return sha256(json.dumps(body,separators=(",",":")).encode()).hexdigest()
