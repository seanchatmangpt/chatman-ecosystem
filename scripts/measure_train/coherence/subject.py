from dataclasses import dataclass
import re

_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

class Refusal(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"REFUSED[{code}]")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self):
        if not _REPO.fullmatch(self.repo): raise Refusal("INVALID_REPOSITORY")
        if not _SHA.fullmatch(self.sha): raise Refusal("INEXACT_SUBJECT")
    @property
    def key(self): return f"{self.repo}@{self.sha}"
