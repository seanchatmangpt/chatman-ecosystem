import re
from dataclasses import dataclass
from .errors import Refused

_SHA = re.compile(r"^[0-9a-f]{40}$")

@dataclass(frozen=True)
class Subject:
    repo: str
    sha: str

    def __post_init__(self):
        if "/" not in self.repo or not _SHA.match(self.sha):
            raise Refused("INEXACT_SUBJECT", f"{self.repo}@{self.sha}")

    @property
    def identity(self) -> str:
        return f"{self.repo}@{self.sha}"
