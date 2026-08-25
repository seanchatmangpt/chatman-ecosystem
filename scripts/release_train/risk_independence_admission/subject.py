from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self):
        if self.repo.count('/') != 1 or not all(self.repo.split('/')):
            raise Refused('INVALID_REPOSITORY_SUBJECT')
        if len(self.sha) != 40 or any(c not in '0123456789abcdef' for c in self.sha):
            raise Refused('INVALID_EXACT_SHA')
    @property
    def exact(self): return f"{self.repo}@{self.sha}"
