from dataclasses import dataclass
import re
from .refusals import Refused

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-f]{40}$")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str

    def __post_init__(self):
        if not _REPO.fullmatch(self.repo) or not _SHA.fullmatch(self.sha):
            raise Refused("INEXACT_SUBJECT", f"{self.repo}@{self.sha}")

    @property
    def identity(self) -> str:
        return f"{self.repo}@{self.sha}"
