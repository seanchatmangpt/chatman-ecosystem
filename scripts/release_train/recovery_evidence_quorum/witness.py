from dataclasses import dataclass
from datetime import datetime,timezone
from .source import EvidenceSource
OUTCOMES={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}
@dataclass(frozen=True)
class RecoveryWitness:
    attempt_id:str; source:EvidenceSource; evidence_id:str; outcome:str; scope:str; observed_at:datetime
    def __post_init__(self):
        if not self.attempt_id or not self.evidence_id or self.outcome not in OUTCOMES or not self.scope:
            raise ValueError("REFUSED[INVALID_WITNESS]")
        if self.observed_at.tzinfo is None: raise ValueError("REFUSED[NAIVE_WITNESS_TIME]")
    @property
    def utc(self): return self.observed_at.astimezone(timezone.utc)
