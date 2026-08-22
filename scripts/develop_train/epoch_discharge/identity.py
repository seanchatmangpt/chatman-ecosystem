from __future__ import annotations
from dataclasses import dataclass
import re

_SUBJECT_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

@dataclass(frozen=True, slots=True)
class Subject:
    value: str
    def __post_init__(self) -> None:
        if not _SUBJECT_RE.fullmatch(self.value):
            raise ValueError("REFUSED[INEXACT_SUBJECT]")
    @property
    def repo(self) -> str:
        return self.value.split("@", 1)[0]
    @property
    def sha(self) -> str:
        return self.value.rsplit("@", 1)[1]
