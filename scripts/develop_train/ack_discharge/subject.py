from dataclasses import dataclass
import re
_SHA=re.compile(r'^[0-9a-f]{40}$'); _REPO=re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
class RefusedSubject(ValueError): pass
@dataclass(frozen=True,slots=True,order=True)
class Subject:
 repo:str; sha:str
 def __post_init__(self):
  if not _REPO.fullmatch(self.repo): raise RefusedSubject('REFUSED[INVALID_REPOSITORY_IDENTITY]')
  if not _SHA.fullmatch(self.sha): raise RefusedSubject('REFUSED[INEXACT_SUBJECT_SHA]')
 @property
 def identity(self): return f'{self.repo}@{self.sha}'
