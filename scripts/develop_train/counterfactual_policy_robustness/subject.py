from dataclasses import dataclass
import re
from .errors import Refused

_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

@dataclass(frozen=True, slots=True)
class Subject:
    value: str
    def __post_init__(self):
        if not _PATTERN.fullmatch(self.value):
            raise Refused("REFUSED_INEXACT_SUBJECT")
