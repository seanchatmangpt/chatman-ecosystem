from __future__ import annotations
from dataclasses import dataclass
import re
_EXACT = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
class Refusal(ValueError):
    pass
@dataclass(frozen=True, slots=True)
class Subject:
    coordinate: str
    def __post_init__(self) -> None:
        if not _EXACT.fullmatch(self.coordinate):
            raise Refusal("REFUSED[INEXACT_SUBJECT]")
    @property
    def repository(self) -> str:
        return self.coordinate.split("@", 1)[0]
    @property
    def sha(self) -> str:
        return self.coordinate.rsplit("@", 1)[1]
