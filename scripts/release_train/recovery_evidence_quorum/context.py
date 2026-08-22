import hashlib,json
from dataclasses import dataclass
from .subject import Subject
@dataclass(frozen=True)
class RecoveryContext:
    subject:Subject; generation:int; cut_id:str; policy_digest:str; frontier_digest:str
    def __post_init__(self):
        if self.generation < 0 or not all((self.cut_id,self.policy_digest,self.frontier_digest)):
            raise ValueError("REFUSED[INVALID_RECOVERY_CONTEXT]")
    @property
    def digest(self):
        b=json.dumps([self.subject.key,self.generation,self.cut_id,self.policy_digest,self.frontier_digest],separators=(",",":"))
        return hashlib.sha256(b.encode()).hexdigest()
