from dataclasses import dataclass
from datetime import datetime
import hashlib
from .subject import Refusal, Subject
from .window import utc

@dataclass(frozen=True)
class EvidenceSource:
    producer: str
    run_id: str
    artifact_id: str
    family: str
    def __post_init__(self) -> None:
        if not all((self.producer,self.run_id,self.artifact_id,self.family)): raise Refusal('REFUSED[INCOMPLETE_EVIDENCE_SOURCE]')
    @property
    def fingerprint(self) -> str:
        return hashlib.sha256('|'.join((self.producer,self.run_id,self.artifact_id,self.family)).encode()).hexdigest()

@dataclass(frozen=True)
class RecoveryWitness:
    subject: Subject
    attempt_id: str
    source: EvidenceSource
    source_id: str
    outcome: str
    observed_at: datetime
    regime_generation: int
    model_digest: str
    def __post_init__(self) -> None:
        if self.outcome not in {'PASS','FAIL','PENDING','UNKNOWN','UNSUPPORTED'}: raise Refusal('REFUSED[INVALID_WITNESS_OUTCOME]')
        if self.regime_generation < 0 or len(self.model_digest)!=64: raise Refusal('REFUSED[INVALID_WITNESS_REGIME]')
        if not self.attempt_id or not self.source_id: raise Refusal('REFUSED[INCOMPLETE_WITNESS]')
        object.__setattr__(self,'observed_at',utc(self.observed_at))
