from __future__ import annotations
from dataclasses import dataclass
import re

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-f]{40}$")

class SubjectRefusal(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str

    @classmethod
    def admit(cls, repo: str, sha: str) -> "Subject":
        if not _REPO.fullmatch(repo):
            raise SubjectRefusal("REFUSED[INVALID_REPOSITORY_IDENTITY]")
        if not _SHA.fullmatch(sha):
            raise SubjectRefusal("REFUSED[INVALID_EXACT_SHA]")
        return cls(repo=repo, sha=sha)
