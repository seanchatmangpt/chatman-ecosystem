from dataclasses import dataclass
from .refusal import refuse
@dataclass(frozen=True)
class Subject:
    repository:str; sha:str; semantic_digest:str; generation:int
    def __post_init__(self):
        if "/" not in self.repository: refuse("INVALID_REPOSITORY")
        if len(self.sha)!=40 or any(c not in "0123456789abcdef" for c in self.sha): refuse("INVALID_SHA")
        if not self.semantic_digest: refuse("EMPTY_SEMANTIC_DIGEST")
        if self.generation<0: refuse("INVALID_GENERATION")
    @property
    def key(self): return f"{self.repository}@{self.sha}#{self.semantic_digest}:g{self.generation}"
