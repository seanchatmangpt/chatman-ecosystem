from __future__ import annotations

from dataclasses import dataclass
import re

SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class Refused(ValueError):
    """Typed fail-closed refusal for inadmissible release evidence."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))


@dataclass(frozen=True, order=True)
class ExactSubject:
    repo: str
    sha: str

    def __post_init__(self) -> None:
        if not REPO.fullmatch(self.repo):
            raise Refused("INVALID_REPOSITORY", self.repo)
        if not SHA40.fullmatch(self.sha):
            raise Refused("NON_EXACT_SUBJECT", self.sha)

    @property
    def coordinate(self) -> str:
        return f"{self.repo}@{self.sha}"
