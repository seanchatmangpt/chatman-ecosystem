from dataclasses import dataclass
import re
from .refusal import require

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    semantic_digest: str

    def __post_init__(self) -> None:
        require(bool(_REPO.fullmatch(self.repo)), "INVALID_REPOSITORY", self.repo)
        require(bool(_HEX40.fullmatch(self.sha)), "INVALID_SHA", self.sha)
        require(bool(_HEX64.fullmatch(self.semantic_digest)), "INVALID_SEMANTIC_DIGEST")

    @property
    def identity(self) -> str:
        return f"{self.repo}@{self.sha}#{self.semantic_digest}"
