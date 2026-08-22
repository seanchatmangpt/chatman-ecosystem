from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .epoch import Epoch
from .subject import Subject

Outcome = Literal["PASS", "FAIL", "PENDING", "UNKNOWN", "UNSUPPORTED"]
Scope = Literal["FOCUSED", "RUNTIME", "REPOSITORY", "DEPENDENCY", "RECEIPT"]

class Refusal(ValueError):
    pass

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    subject: Subject
    scope: Scope
    outcome: Outcome
    observed_at: datetime
    run_id: str | None = None
    artifact_id: str | None = None

    def admit(self, epoch: Epoch) -> "Evidence":
        if not self.evidence_id.strip():
            raise Refusal("REFUSED[EMPTY_EVIDENCE_ID]")
        if self.scope in {"FOCUSED", "RUNTIME", "REPOSITORY"} and not self.run_id:
            raise Refusal("REFUSED[MISSING_RUN_ID]")
        if self.scope == "RECEIPT" and not self.artifact_id:
            raise Refusal("REFUSED[MISSING_ARTIFACT_ID]")
        if not epoch.contains(self.observed_at):
            raise Refusal("REFUSED[EVIDENCE_OUTSIDE_EPOCH]")
        return self
