from dataclasses import dataclass
import re
from .errors import Refused
_RE=re.compile(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)@([0-9a-f]{40})$")
@dataclass(frozen=True)
class Subject:
    owner:str; repo:str; sha:str
    @classmethod
    def parse(cls, value:str):
        m=_RE.fullmatch(value)
        if not m: raise Refused("INEXACT_SUBJECT")
        return cls(*m.groups())
    @property
    def key(self): return f"{self.owner}/{self.repo}@{self.sha}"
