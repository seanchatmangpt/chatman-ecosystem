from dataclasses import dataclass
from datetime import datetime, timezone
from .subject import Refused
ALLOWED={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}
@dataclass(frozen=True)
class RecoveryWitness:
    attempt_id: str; source_fingerprint: str; outcome: str; observed_at: datetime; scope: str="REPOSITORY"
    def __post_init__(self):
        if self.outcome not in ALLOWED: raise Refused("REFUSED[INVALID_WITNESS_OUTCOME]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_WITNESS_TIME]")
        if not self.attempt_id or len(self.source_fingerprint)!=64: raise Refused("REFUSED[INVALID_WITNESS_IDENTITY]")
    def utc(self): return self.observed_at.astimezone(timezone.utc)
