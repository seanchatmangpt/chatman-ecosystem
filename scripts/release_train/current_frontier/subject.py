from __future__ import annotations

import re
from dataclasses import dataclass

_SUBJECT_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

class Refusal(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str

    @classmethod
    def parse(cls, value: str) -> "Subject":
        if not _SUBJECT_RE.fullmatch(value):
            raise Refusal("REFUSED[INEXACT_SUBJECT]")
        repo, sha = value.rsplit("@", 1)
        return cls(repo=repo, sha=sha)

    def canonical(self) -> str:
        return f"{self.repo}@{self.sha}"
