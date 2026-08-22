from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json

from .subject import Refused, Subject


class WitnessOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    producer: str
    run_id: str
    artifact_digest: str
    family: str

    def __post_init__(self) -> None:
        if not self.producer or not self.run_id or not self.family:
            raise Refused("REFUSED[INCOMPLETE_EVIDENCE_SOURCE]")
        if len(self.artifact_digest) != 64 or any(c not in "0123456789abcdef" for c in self.artifact_digest):
            raise Refused("REFUSED[INVALID_ARTIFACT_DIGEST]")

    @property
    def fingerprint(self) -> str:
        body = json.dumps({"producer": self.producer, "run": self.run_id, "artifact": self.artifact_digest, "family": self.family}, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True, slots=True)
class RecoveryWitness:
    evidence_id: str
    subject: Subject
    attempt_id: str
    source: EvidenceSource
    scope: str
    outcome: WitnessOutcome
    observed_at: datetime

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.attempt_id or not self.scope:
            raise Refused("REFUSED[INCOMPLETE_RECOVERY_WITNESS]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_WITNESS_TIME]")
