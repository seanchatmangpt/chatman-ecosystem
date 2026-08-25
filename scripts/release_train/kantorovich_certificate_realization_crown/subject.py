import re
from dataclasses import dataclass
from .refusal import Refused
PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
@dataclass(frozen=True)
class Subject:
    identity: str
    @classmethod
    def parse(cls, identity: str):
        if not PATTERN.match(identity):
            raise Refused("INVALID_EXACT_SUBJECT")
        return cls(identity)
