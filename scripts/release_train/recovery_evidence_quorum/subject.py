import re
from dataclasses import dataclass
HEX40=re.compile(r"^[0-9a-f]{40}$")
@dataclass(frozen=True)
class Subject:
    repo:str
    sha:str
    def __post_init__(self):
        if "/" not in self.repo or not HEX40.fullmatch(self.sha):
            raise ValueError("REFUSED[INEXACT_SUBJECT]")
    @property
    def key(self): return f"{self.repo}@{self.sha}"
