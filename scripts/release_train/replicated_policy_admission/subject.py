from dataclasses import dataclass
import re
from .refusal import Refused

_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str

    def __post_init__(self) -> None:
        if not _REPO.fullmatch(self.repo):
            raise Refused("INEXACT_REPOSITORY", self.repo)
        if not _SHA.fullmatch(self.sha):
            raise Refused("INEXACT_SUBJECT", self.sha)

    @property
    def identity(self) -> str:
        return f"{self.repo}@{self.sha}"
