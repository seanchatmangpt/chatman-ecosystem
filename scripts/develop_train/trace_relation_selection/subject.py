from dataclasses import dataclass
import re
from .refusal import Refused

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True, order=True)
class Subject:
    repository: str
    sha: str
    semantic_digest: str

    @classmethod
    def parse(cls, repository: str, sha: str, semantic_digest: str) -> "Subject":
        if repository.count("/") != 1 or any(not p for p in repository.split("/")):
            raise Refused("REFUSED[INVALID_REPOSITORY]")
        if not _HEX40.fullmatch(sha):
            raise Refused("REFUSED[INEXACT_SUBJECT_SHA]")
        if not _HEX64.fullmatch(semantic_digest):
            raise Refused("REFUSED[INVALID_SEMANTIC_DIGEST]")
        return cls(repository, sha, semantic_digest)

    @property
    def key(self) -> str:
        return f"{self.repository}@{self.sha}:{self.semantic_digest}"
