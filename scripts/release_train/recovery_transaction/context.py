from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, re
from .subject import Subject, Refusal
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

def _canon(v: object) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":")).encode()

@dataclass(frozen=True)
class RecoveryContext:
    subject: Subject
    generation: int
    cut_id: str
    policy_digest: str
    frontier_digest: str
    strategy: str
    def __post_init__(self) -> None:
        if self.generation < 0 or not self.cut_id or not _HEX64.fullmatch(self.policy_digest) or not _HEX64.fullmatch(self.frontier_digest) or not self.strategy:
            raise Refusal("REFUSED[INVALID_RECOVERY_CONTEXT]")
    @property
    def digest(self) -> str:
        return hashlib.sha256(_canon({"subject":self.subject.exact_id,"generation":self.generation,"cut_id":self.cut_id,"policy":self.policy_digest,"frontier":self.frontier_digest,"strategy":self.strategy})).hexdigest()
