import re
from dataclasses import dataclass
from .errors import Refused

_RX = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

@dataclass(frozen=True)
class Subject:
    key: str
    @classmethod
    def parse(cls, value: str):
        if not _RX.fullmatch(value):
            raise Refused("INEXACT_SUBJECT")
        return cls(value)
