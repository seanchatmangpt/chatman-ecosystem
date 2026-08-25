from __future__ import annotations
from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str

    @classmethod
    def parse(cls, value: str) -> "Subject":
        if "@" not in value:
            raise Refused("SUBJECT_FORMAT")
        repo, sha = value.rsplit("@", 1)
        if repo.count("/") != 1 or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            raise Refused("INEXACT_SUBJECT", value)
        return cls(repo, sha)

    def canonical(self) -> str:
        return f"{self.repo}@{self.sha}"
