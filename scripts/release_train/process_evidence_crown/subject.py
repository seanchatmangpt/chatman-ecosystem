from dataclasses import dataclass
import re
from .refusal import Refused

_REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_HEX40=re.compile(r"^[0-9a-f]{40}$")
_HEX64=re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    semantic_digest: str
    @classmethod
    def parse(cls, repo: str, sha: str, semantic_digest: str):
        if not _REPO.fullmatch(repo): raise Refused("INVALID_REPOSITORY", repo)
        if not _HEX40.fullmatch(sha): raise Refused("INVALID_SUBJECT_SHA", sha)
        if not _HEX64.fullmatch(semantic_digest): raise Refused("INVALID_SEMANTIC_DIGEST")
        return cls(repo, sha, semantic_digest)
    @property
    def key(self): return f"{self.repo}@{self.sha}#{self.semantic_digest}"
