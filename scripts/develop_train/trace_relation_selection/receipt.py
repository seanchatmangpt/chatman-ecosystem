from dataclasses import dataclass
import hashlib, json
from .refusal import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str
    generation: int
    strongest: tuple[str, ...]
    standing: str
    authority: str = "SELECT"
    actuation_performed: bool = False

    def __post_init__(self):
        if self.actuation_performed:
            raise Refused("REFUSED[REPORTED_AMBIENT_ACTUATION]")

    @property
    def body(self):
        return {
            "schema": "chatman.develop-trace-relation-selection/1",
            "subject": self.subject,
            "generation": self.generation,
            "strongest": list(self.strongest),
            "standing": self.standing,
            "authority": self.authority,
            "actuation_performed": self.actuation_performed,
        }

    @property
    def digest(self):
        raw = json.dumps(self.body, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

def replay(receipt: Receipt, expected_digest: str) -> bool:
    if receipt.actuation_performed:
        raise Refused("REFUSED[REPLAY_REPORTS_ACTUATION]")
    if receipt.digest != expected_digest:
        raise Refused("REFUSED[RECEIPT_DIGEST_MISMATCH]")
    return True
