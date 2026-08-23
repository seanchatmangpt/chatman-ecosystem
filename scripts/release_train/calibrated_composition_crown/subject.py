from dataclasses import dataclass
import re
from .refusal import Refused
@dataclass(frozen=True)
class Subject:
    repo:str; sha:str; semantic_digest:str
    @classmethod
    def parse(cls, repo, sha, semantic_digest):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo): raise Refused("INVALID_SUBJECT")
        if not re.fullmatch(r"[0-9a-f]{40}", sha): raise Refused("INVALID_SUBJECT")
        if not re.fullmatch(r"[0-9a-f]{64}", semantic_digest): raise Refused("INVALID_SEMANTIC_DIGEST")
        return cls(repo,sha,semantic_digest)
    @property
    def key(self): return f"{self.repo}@{self.sha}#{self.semantic_digest}"
