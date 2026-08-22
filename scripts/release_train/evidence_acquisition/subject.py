import re
from dataclasses import dataclass

_EXACT = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    @classmethod
    def parse(cls, value: str) -> "Subject":
        if not _EXACT.fullmatch(value):
            raise ValueError("REFUSED[INEXACT_SUBJECT]")
        repo, sha = value.split("@", 1)
        return cls(repo, sha)
    def canonical(self) -> str:
        return f"{self.repo}@{self.sha}"
