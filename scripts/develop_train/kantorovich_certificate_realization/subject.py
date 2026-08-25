from dataclasses import dataclass
import re
from .errors import Refused

_PATTERN = re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})#(?P<semantic>[0-9a-f]{64})$")

@dataclass(frozen=True, order=True)
class Subject:
    repository: str
    sha: str
    semantic_digest: str

    @classmethod
    def parse(cls, value: str) -> "Subject":
        match = _PATTERN.fullmatch(value.strip())
        if not match:
            raise Refused("INEXACT_SUBJECT", value)
        return cls(match.group("repo"), match.group("sha"), match.group("semantic"))

    @property
    def key(self) -> str:
        return f"{self.repository}@{self.sha}#{self.semantic_digest}"
