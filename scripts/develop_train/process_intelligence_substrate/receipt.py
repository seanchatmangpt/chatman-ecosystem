from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from .errors import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str
    semantic_digest: str
    standing: str
    rails: tuple[str, ...]
    actuation_performed: bool = False

    def body(self) -> dict[str, object]:
        if self.actuation_performed:
            raise Refused("REPORTED_ACTUATION")
        return asdict(self)

    def digest(self) -> str:
        payload = json.dumps(self.body(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()


def replay(receipt: Receipt, digest: str) -> bool:
    return receipt.digest() == digest
