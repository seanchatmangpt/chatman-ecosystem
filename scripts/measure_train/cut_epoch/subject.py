import re
from dataclasses import dataclass
class Refused(ValueError): pass
@dataclass(frozen=True, order=True)
class Subject:
    repo:str
    sha:str
    def __post_init__(self):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repo): raise Refused("REFUSED[INVALID_REPOSITORY]")
        if not re.fullmatch(r"[0-9a-f]{40}", self.sha): raise Refused("REFUSED[INEXACT_SUBJECT]")
