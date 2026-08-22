from __future__ import annotations
from dataclasses import dataclass
import re

_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

class Refusal(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self) -> None:
        if not _REPO.fullmatch(self.repo) or not _SHA.fullmatch(self.sha):
            raise Refusal("REFUSED[INEXACT_SUBJECT]")
    @property
    def exact_id(self) -> str:
        return f"{self.repo}@{self.sha}"
