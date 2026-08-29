from dataclasses import dataclass
import re
from .errors import Refused
_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
@dataclass(frozen=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self):
        if not _REPO.fullmatch(self.repo) or not _SHA.fullmatch(self.sha):
            raise Refused("INEXACT_SUBJECT", f"{self.repo}@{self.sha}")
    @property
    def exact(self): return f"{self.repo}@{self.sha}"
