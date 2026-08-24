from dataclasses import dataclass
import re
from .errors import Refused
_RE = re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})$")
@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    @classmethod
    def parse(cls, raw: str):
        m = _RE.fullmatch(raw.strip())
        if not m: raise Refused("INEXACT_SUBJECT", raw)
        return cls(m.group("repo"), m.group("sha"))
    @property
    def key(self): return f"{self.repo}@{self.sha}"
