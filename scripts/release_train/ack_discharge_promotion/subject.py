from __future__ import annotations
from dataclasses import dataclass
import re

_SUBJECT_RE = re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})$")

class SubjectRefusal(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str

    @classmethod
    def parse(cls, value: str) -> "Subject":
        match = _SUBJECT_RE.fullmatch(value)
        if not match:
            raise SubjectRefusal("REFUSED[INEXACT_SUBJECT]")
        return cls(match.group("repo"), match.group("sha"))

    def render(self) -> str:
        return f"{self.repo}@{self.sha}"
