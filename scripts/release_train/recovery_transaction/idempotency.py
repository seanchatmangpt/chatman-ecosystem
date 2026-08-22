from __future__ import annotations
from dataclasses import dataclass, field
from .subject import Refusal
@dataclass
class IdempotencyLedger:
    seen: dict[str,str]=field(default_factory=dict)
    def admit(self, key:str, payload_digest:str)->bool:
        if not key or len(payload_digest)!=64: raise Refusal("REFUSED[INVALID_IDEMPOTENCY_KEY]")
        prior=self.seen.get(key)
        if prior is None: self.seen[key]=payload_digest; return True
        if prior!=payload_digest: raise Refusal("REFUSED[IDEMPOTENCY_CONFLICT]")
        return False
