from dataclasses import dataclass
import hashlib
import json
from .errors import Refused


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

@dataclass(frozen=True)
class Receipt:
    subject: str
    certificate_digest: str
    calibration_digest: str
    standing: str
    authority: str = "VERIFY"
    actuation_performed: bool = False

    def __post_init__(self) -> None:
        if self.authority not in {"OBSERVE", "SELECT", "CONSTRUCT", "VERIFY"}:
            raise Refused("INVALID_RECEIPT_AUTHORITY")
        if self.actuation_performed:
            raise Refused("REPORTED_AMBIENT_ACTUATION")

    @property
    def body(self):
        return {
            "schema": "chatman.develop-kantorovich-certificate-realization/1",
            "subject": self.subject,
            "certificate_digest": self.certificate_digest,
            "calibration_digest": self.calibration_digest,
            "standing": self.standing,
            "authority": self.authority,
            "actuation_performed": self.actuation_performed,
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical(self.body).encode()).hexdigest()
