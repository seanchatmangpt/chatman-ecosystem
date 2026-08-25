from __future__ import annotations
from dataclasses import dataclass
import re
from .refusal import Refused

_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    semantic_digest: str

    def __post_init__(self) -> None:
        if not _REPO.fullmatch(self.repo):
            raise Refused("INVALID_REPOSITORY_SUBJECT", self.repo)
        if not _SHA.fullmatch(self.sha):
            raise Refused("INEXACT_SUBJECT_SHA", self.sha)
        if not _SHA.fullmatch(self.semantic_digest):
            raise Refused("INVALID_SEMANTIC_DIGEST", self.semantic_digest)

    @property
    def key(self) -> str:
        return f"{self.repo}@{self.sha}#{self.semantic_digest}"
