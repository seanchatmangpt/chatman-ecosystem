from dataclasses import dataclass
import hashlib
import json

from .errors import Refused


@dataclass(frozen=True)
class Receipt:
    subject: str
    strategy: str
    decision: str
    generation: int
    standing: str
    replay_root: str
    authority: str = "SELECT"
    actuation_performed: bool = False

    def body(self):
        return {key: getattr(self, key) for key in ("subject", "strategy", "decision", "generation", "standing", "replay_root", "authority", "actuation_performed")}

    def digest(self):
        payload = json.dumps(self.body(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()


def replay(receipt: Receipt, digest: str):
    if receipt.actuation_performed:
        raise Refused("REPORTED_AMBIENT_ACTUATION")
    if receipt.authority != "SELECT" or receipt.digest() != digest:
        raise Refused("REPLAY_MISMATCH")
    return "REPLAY_MATCH"
