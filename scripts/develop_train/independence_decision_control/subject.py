from dataclasses import dataclass
import re

from .errors import Refused

PAT = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}#[0-9a-f]{64}$")


@dataclass(frozen=True)
class Subject:
    key: str

    @classmethod
    def parse(cls, value: str):
        if not PAT.fullmatch(value):
            raise Refused("INVALID_SUBJECT")
        return cls(value)
