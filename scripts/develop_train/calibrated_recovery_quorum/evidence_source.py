from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    producer: str
    run_id: str
    artifact_id: str
    family: str

    def __post_init__(self) -> None:
        if not all(v.strip() for v in (self.producer, self.run_id, self.artifact_id, self.family)):
            raise ValueError("REFUSED[INCOMPLETE_EVIDENCE_SOURCE]")

    @property
    def fingerprint(self) -> str:
        body = json.dumps(
            {
                "artifact": self.artifact_id,
                "family": self.family,
                "producer": self.producer,
                "run": self.run_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(body.encode()).hexdigest()
