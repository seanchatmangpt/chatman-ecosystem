from dataclasses import dataclass
import re
from .refusal import Refused

_SHA = re.compile(r"^[0-9a-f]{40}$")

@dataclass(frozen=True, order=True)
class SubjectEpoch:
    repo: str
    sha: str
    generation: int
    semantic_digest: str

    def __post_init__(self) -> None:
        if "/" not in self.repo or not _SHA.fullmatch(self.sha):
            raise Refused("INEXACT_SUBJECT", f"{self.repo}@{self.sha}")
        if self.generation < 0:
            raise Refused("INVALID_GENERATION")
        if not self.semantic_digest:
            raise Refused("MISSING_SEMANTIC_DIGEST")

    def advance(self, sha: str, semantic_digest: str) -> "SubjectEpoch":
        if sha == self.sha:
            raise Refused("NONADVANCING_SUBJECT")
        return SubjectEpoch(self.repo, sha, self.generation + 1, semantic_digest)
