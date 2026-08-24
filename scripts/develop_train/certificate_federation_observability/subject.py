from dataclasses import dataclass
import re
from .errors import Refused
RX=re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})#(?P<semantic>[0-9a-f]{64})$")
@dataclass(frozen=True, order=True)
class Subject:
    repo:str; sha:str; semantic:str
    @classmethod
    def parse(cls,s):
        m=RX.fullmatch(s.strip())
        if not m: raise Refused("INEXACT_SUBJECT",s)
        return cls(m.group("repo"),m.group("sha"),m.group("semantic"))
    @property
    def key(self): return f"{self.repo}@{self.sha}#{self.semantic}"
