from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .subject import Subject, Refusal

def digest_json(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()

@dataclass(frozen=True)
class RecoveryContext:
    subject: Subject
    generation: int
    cut_id: str
    policy_digest: str
    frontier_digest: str
    strategy: str
    def __post_init__(self) -> None:
        if self.generation < 0:
            raise Refusal("INVALID_GENERATION", "generation must be non-negative")
        for name, value in (("cut_id", self.cut_id), ("policy_digest", self.policy_digest), ("frontier_digest", self.frontier_digest), ("strategy", self.strategy)):
            if not isinstance(value, str) or not value.strip():
                raise Refusal("INVALID_CONTEXT", f"{name} must be non-empty")
    @property
    def digest(self) -> str:
        return digest_json({"subject": self.subject.identity, "generation": self.generation, "cut_id": self.cut_id, "policy_digest": self.policy_digest, "frontier_digest": self.frontier_digest, "strategy": self.strategy})
