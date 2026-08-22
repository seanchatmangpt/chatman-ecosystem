from __future__ import annotations
from dataclasses import dataclass
import re

_SHA = re.compile(r"^[0-9a-f]{40}$")
_COORD = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

class Refusal(ValueError):
    code: str
    def __init__(self, code: str, detail: str):
        super().__init__(f"REFUSED[{code}]: {detail}")
        self.code = code
        self.detail = detail

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self) -> None:
        if not _COORD.fullmatch(self.repo):
            raise Refusal("INEXACT_SUBJECT", f"invalid repo coordinate {self.repo!r}")
        if not _SHA.fullmatch(self.sha):
            raise Refusal("INEXACT_SUBJECT", "sha must be exact lowercase 40-hex")
    @property
    def identity(self) -> str:
        return f"{self.repo}@{self.sha}"
