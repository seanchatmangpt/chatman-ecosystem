from dataclasses import dataclass
import re
from .errors import Refused

_SUBJECT = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

@dataclass(frozen=True, order=True)
class Subject:
    value: str
    def __post_init__(self):
        if not _SUBJECT.fullmatch(self.value):
            raise Refused("INEXACT_SUBJECT")
    def canonical(self) -> str:
        return self.value
