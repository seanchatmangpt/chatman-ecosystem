from dataclasses import dataclass
import re
from .errors import Refused
_RE = re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})#(?P<semantic>[0-9a-f]{64})$")
@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    semantic: str
    @classmethod
    def parse(cls, value: str):
        m=_RE.fullmatch(value or "")
        if not m: raise Refused("INVALID_SUBJECT", value)
        return cls(m["repo"],m["sha"],m["semantic"])
    @property
    def key(self): return f"{self.repo}@{self.sha}#{self.semantic}"
