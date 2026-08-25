import re
from dataclasses import dataclass
from .refusals import Refused
@dataclass(frozen=True, order=True)
class Subject:
    repo:str; sha:str; semantic_digest:str; generation:int
    def __post_init__(self):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',self.repo): raise Refused('REFUSED[INVALID_REPOSITORY]')
        if not re.fullmatch(r'[0-9a-f]{40}',self.sha): raise Refused('REFUSED[INEXACT_SUBJECT]')
        if not re.fullmatch(r'[0-9a-f]{64}',self.semantic_digest): raise Refused('REFUSED[INVALID_SEMANTIC_DIGEST]')
        if self.generation<0: raise Refused('REFUSED[INVALID_GENERATION]')
