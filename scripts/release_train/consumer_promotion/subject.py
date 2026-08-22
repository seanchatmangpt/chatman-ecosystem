from dataclasses import dataclass
import re
_RX=re.compile(r"^[0-9a-f]{40}$")
@dataclass(frozen=True, order=True)
class Subject:
    repo:str
    sha:str
    def __post_init__(self):
        if "/" not in self.repo or self.repo.startswith("/") or self.repo.endswith("/"):
            raise ValueError("REFUSED[INVALID_REPO]")
        if not _RX.fullmatch(self.sha):
            raise ValueError("REFUSED[INEXACT_SHA]")
    @property
    def key(self): return f"{self.repo}@{self.sha}"
