from dataclasses import dataclass
import re
_SHA=re.compile(r'^[0-9a-f]{40}$'); _REPO=re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
class Refusal(ValueError): pass
@dataclass(frozen=True, slots=True)
class Subject:
    repo:str; sha:str
    def __post_init__(self):
        if not _REPO.fullmatch(self.repo) or not _SHA.fullmatch(self.sha): raise Refusal('REFUSED_INEXACT_SUBJECT')
    @property
    def key(self): return f'{self.repo}@{self.sha}'
