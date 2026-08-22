from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .subject import Subject
from .window import ObservationWindow

_ALLOWED = {"success", "failure", "cancelled", "queued", "in_progress", "unknown"}

class EvidenceRefusal(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Evidence:
    key: str
    subject: Subject
    observed_at: str
    status: str
    source: str

    @classmethod
    def admit(cls, *, key: str, repo: str, sha: str, observed_at: str, status: str, source: str,
              window: ObservationWindow) -> "Evidence":
        subject = Subject.admit(repo, sha)
        if not key.strip() or not source.strip():
            raise EvidenceRefusal("REFUSED[EMPTY_EVIDENCE_IDENTITY]")
        if status not in _ALLOWED:
            raise EvidenceRefusal("REFUSED[INVALID_EVIDENCE_STATUS]")
        if not window.contains(observed_at):
            raise EvidenceRefusal("REFUSED[OUTSIDE_OBSERVATION_WINDOW]")
        return cls(key, subject, observed_at, status, source)

def standing(rows: Iterable[Evidence]) -> str:
    rows = tuple(rows)
    if not rows or any(r.status in {"queued", "in_progress", "unknown"} for r in rows):
        return "UNKNOWN"
    if any(r.status in {"failure", "cancelled"} for r in rows):
        return "BUILD_BROKEN"
    return "PARTIAL_ALIVE"
