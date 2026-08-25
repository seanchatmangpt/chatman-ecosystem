from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
import re

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-f]{40}$")

class Standing(StrEnum):
    UNKNOWN="UNKNOWN"; PARTIAL_ALIVE="PARTIAL_ALIVE"; ALIVE="ALIVE"; BLOCKED="BLOCKED"; BUILD_BROKEN="BUILD_BROKEN"; UNSUPPORTED="UNSUPPORTED"

class RefusalCode(StrEnum):
    INVALID_SUBJECT="INVALID_SUBJECT"; STALE_OR_FOREIGN_SUBJECT="STALE_OR_FOREIGN_SUBJECT"; INVALID_WINDOW="INVALID_WINDOW"; EVIDENCE_STALE="EVIDENCE_STALE"; EVIDENCE_FUTURE="EVIDENCE_FUTURE"; CONFLICTING_EVIDENCE="CONFLICTING_EVIDENCE"; RECEIPT_MISMATCH="RECEIPT_MISMATCH"; DEPENDENCY_CYCLE="DEPENDENCY_CYCLE"; AUTHORITY_VIOLATION="AUTHORITY_VIOLATION"

class Refused(ValueError):
    def __init__(self, code: RefusalCode, detail: str):
        self.code=code; self.detail=detail
        super().__init__(f"REFUSED[{code}]: {detail}")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self):
        if not _REPO.fullmatch(self.repo) or not _SHA.fullmatch(self.sha):
            raise Refused(RefusalCode.INVALID_SUBJECT, f"{self.repo}@{self.sha}")
    @property
    def identity(self)->str: return f"{self.repo}@{self.sha}"
