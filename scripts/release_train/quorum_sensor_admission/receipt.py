from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json

from .errors import Refused


SCHEMA = "chatman.quorum-sensor-admission/1"


@dataclass(frozen=True)
class Receipt:
    subject: str
    calibration_generation: int
    calibration_digest: str
    coverage: str
    topology: str
    strategy: str | None
    blockers: tuple[str, ...]
    standing: str
    reason: str
    authority: str = "SELECT"
    phases: tuple[str, ...] = ("VERIFY", "CONSTRUCT")
    actuation_performed: bool = False
    digest: str = ""

    def body(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "subject": self.subject,
            "calibration_generation": self.calibration_generation,
            "calibration_digest": self.calibration_digest,
            "coverage": self.coverage,
            "topology": self.topology,
            "strategy": self.strategy,
            "blockers": list(self.blockers),
            "standing": self.standing,
            "reason": self.reason,
            "authority": self.authority,
            "phases": list(self.phases),
            "actuation_performed": self.actuation_performed,
        }

    def compute_digest(self) -> str:
        return hashlib.sha256(json.dumps(self.body(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def seal(self) -> "Receipt":
        return replace(self, digest=self.compute_digest())

    def replay(self) -> None:
        if self.authority != "SELECT" or self.phases != ("VERIFY", "CONSTRUCT") or self.actuation_performed:
            raise Refused("RECEIPT_AUTHORITY_DRIFT")
        if self.digest != self.compute_digest():
            raise Refused("RECEIPT_TAMPER")
