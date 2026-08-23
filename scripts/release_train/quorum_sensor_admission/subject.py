from __future__ import annotations

from dataclasses import dataclass
import re

from .errors import Refused

_SHA = re.compile(r"^[0-9a-f]{40}$")
_COORD = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True, order=True)
class Subject:
    repository: str
    sha: str

    @classmethod
    def parse(cls, value: str) -> "Subject":
        try:
            repository, sha = value.rsplit("@", 1)
        except ValueError as exc:
            raise Refused("INVALID_SUBJECT", value) from exc
        if not _COORD.fullmatch(repository) or not _SHA.fullmatch(sha):
            raise Refused("INVALID_SUBJECT", value)
        return cls(repository=repository, sha=sha)

    def canonical(self) -> str:
        return f"{self.repository}@{self.sha}"
