from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True)
class SubjectEpoch:
    repo: str
    sha: str
    generation: int
    semantic_digest: str
    def __post_init__(self):
        if "/" not in self.repo or len(self.sha)!=40 or any(c not in "0123456789abcdef" for c in self.sha): raise Refused("INEXACT_SUBJECT")
        if self.generation < 0 or len(self.semantic_digest) < 16: raise Refused("INVALID_EPOCH")
    def advance(self, sha: str, semantic_digest: str):
        if sha == self.sha: raise Refused("NONADVANCING_SUBJECT")
        return SubjectEpoch(self.repo, sha, self.generation+1, semantic_digest)
