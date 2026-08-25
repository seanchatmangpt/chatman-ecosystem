from dataclasses import dataclass
import re
from .refusal import Refused
_SHA=re.compile(r"^[0-9a-f]{40}$")
@dataclass(frozen=True)
class Subject:
    repo: str; sha: str; semantic: str; generation: int
    def __post_init__(self):
        if "/" not in self.repo or not _SHA.fullmatch(self.sha): raise Refused("INVALID_SUBJECT")
        if not self.semantic.strip() or self.generation < 0: raise Refused("INVALID_SUBJECT")
    @property
    def identity(self): return f"{self.repo}@{self.sha}#{self.semantic}:g{self.generation}"
