from __future__ import annotations

from dataclasses import dataclass
import re

from .model import ExactSubject, Refused
from .window import ObservationWindow

HEX64 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_KINDS = frozenset({"ci_run", "job_log", "artifact", "receipt", "repository_state"})


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    subject: ExactSubject
    kind: str
    observed_at: str
    source_uri: str
    digest_sha256: str
    run_id: int | None = None
    artifact_id: int | None = None

    def admit(self, window: ObservationWindow) -> "EvidenceRecord":
        if not self.evidence_id.strip():
            raise Refused("MISSING_EVIDENCE_ID")
        if self.kind not in ALLOWED_KINDS:
            raise Refused("UNSUPPORTED_EVIDENCE_KIND", self.kind)
        window.require(self.observed_at)
        if not self.source_uri.startswith("https://github.com/") and not self.source_uri.startswith("https://api.github.com/"):
            raise Refused("NON_GITHUB_EVIDENCE_SOURCE", self.source_uri)
        if not HEX64.fullmatch(self.digest_sha256):
            raise Refused("INVALID_EVIDENCE_DIGEST", self.digest_sha256)
        if self.kind in {"ci_run", "job_log", "artifact"} and (self.run_id is None or self.run_id <= 0):
            raise Refused("MISSING_RUN_ID", self.evidence_id)
        if self.kind == "artifact" and (self.artifact_id is None or self.artifact_id <= 0):
            raise Refused("MISSING_ARTIFACT_ID", self.evidence_id)
        return self
