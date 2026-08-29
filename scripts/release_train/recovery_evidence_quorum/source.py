import hashlib,json
from dataclasses import dataclass
@dataclass(frozen=True)
class EvidenceSource:
    producer:str; run_id:str; artifact_id:str; family:str
    def __post_init__(self):
        if not all((self.producer,self.run_id,self.artifact_id,self.family)):
            raise ValueError("REFUSED[INCOMPLETE_EVIDENCE_SOURCE]")
    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps([self.producer,self.run_id,self.artifact_id,self.family],separators=(",",":")).encode()).hexdigest()
