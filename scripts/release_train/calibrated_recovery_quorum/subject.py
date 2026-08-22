from dataclasses import dataclass
import re

class Refused(ValueError): pass

@dataclass(frozen=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self):
        if not re.fullmatch(r"[^/\s]+/[^/\s]+", self.repo):
            raise Refused("REFUSED[INEXACT_REPOSITORY]")
        if not re.fullmatch(r"[0-9a-f]{40}", self.sha):
            raise Refused("REFUSED[INEXACT_SUBJECT]")
    @property
    def exact(self): return f"{self.repo}@{self.sha}"
