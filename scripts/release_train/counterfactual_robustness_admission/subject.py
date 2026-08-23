from dataclasses import dataclass
from .refusal import refuse

@dataclass(frozen=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self):
        if '/' not in self.repo or self.repo.startswith('/') or self.repo.endswith('/'):
            refuse("INEXACT_SUBJECT")
        if len(self.sha)!=40 or any(c not in '0123456789abcdef' for c in self.sha):
            refuse("INEXACT_SUBJECT")
    @property
    def exact(self): return f"{self.repo}@{self.sha}"
