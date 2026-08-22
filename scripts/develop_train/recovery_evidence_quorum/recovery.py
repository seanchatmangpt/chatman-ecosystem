from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timezone

from .subject import Refused, Subject


def _digest(payload: dict[str, object]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True, slots=True)
class RecoveryContext:
    subject: Subject
    generation: int
    cut_id: str
    policy_digest: str
    frontier_digest: str

    def __post_init__(self) -> None:
        if self.generation < 0 or not self.cut_id:
            raise Refused("REFUSED[INVALID_RECOVERY_CONTEXT]")
        for value in (self.policy_digest, self.frontier_digest):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise Refused("REFUSED[INVALID_CONTEXT_DIGEST]")

    @property
    def digest(self) -> str:
        return _digest({
            "subject": self.subject.exact_id,
            "generation": self.generation,
            "cut_id": self.cut_id,
            "policy": self.policy_digest,
            "frontier": self.frontier_digest,
        })


@dataclass(frozen=True, slots=True)
class RecoveryAttempt:
    consumer: Subject
    base_context_digest: str
    target_context_digest: str
    ordinal: int
    issued_at: datetime
    nonce: str

    def __post_init__(self) -> None:
        if self.ordinal < 0 or not self.nonce:
            raise Refused("REFUSED[INVALID_RECOVERY_ATTEMPT]")
        if self.issued_at.tzinfo is None or self.issued_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_ATTEMPT_TIME]")
        for value in (self.base_context_digest, self.target_context_digest):
            if len(value) != 64:
                raise Refused("REFUSED[INVALID_CONTEXT_DIGEST]")

    @property
    def attempt_id(self) -> str:
        return _digest({
            "consumer": self.consumer.exact_id,
            "base": self.base_context_digest,
            "target": self.target_context_digest,
            "ordinal": self.ordinal,
            "issued_at": self.issued_at.astimezone(timezone.utc).isoformat(),
            "nonce": self.nonce,
        })
