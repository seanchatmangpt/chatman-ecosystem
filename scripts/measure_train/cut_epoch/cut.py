from dataclasses import dataclass
import hashlib, json
from .subject import Refused
@dataclass(frozen=True)
class EvidenceCut:
    generation:int
    epochs:tuple
    def __post_init__(self):
        if self.generation < 0: raise Refused("REFUSED[INVALID_CUT_GENERATION]")
        repos=[e.subject.repo for e in self.epochs]
        if len(repos)!=len(set(repos)): raise Refused("REFUSED[DUPLICATE_CUT_REPOSITORY]")
    @property
    def cut_id(self):
        body=[(e.subject.repo,e.subject.sha,e.generation,e.receipt_sha256,e.observed_at.isoformat()) for e in sorted(self.epochs)]
        return hashlib.sha256(json.dumps([self.generation,body],separators=(",",":")).encode()).hexdigest()
    def by_repo(self): return {e.subject.repo:e for e in self.epochs}
