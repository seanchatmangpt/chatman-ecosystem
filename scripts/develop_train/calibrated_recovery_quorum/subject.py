from __future__ import annotations

from dataclasses import dataclass
import re

_EXACT_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True, slots=True)
class Subject:
    repo: str
    sha: str

    def __post_init__(self) -> None:
        if not _REPO.fullmatch(self.repo):
            raise ValueError("REFUSED[INEXACT_REPOSITORY_IDENTITY]")
        if not _EXACT_SHA.fullmatch(self.sha):
            raise ValueError("REFUSED[INEXACT_SUBJECT_SHA]")

    @property
    def exact(self) -> str:
        return f"{self.repo}@{self.sha}"
