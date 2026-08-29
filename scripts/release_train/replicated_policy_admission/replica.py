from dataclasses import dataclass
from hashlib import sha256
import json
from .subject import Subject
from .vector_clock import VectorClock
from .refusal import Refused

@dataclass(frozen=True)
class ReplicaPolicyState:
    replica_id: str
    subject: Subject
    generation: int
    policy_digest: str
    frontier_digest: str
    clock: VectorClock

    def __post_init__(self) -> None:
        if not self.replica_id: raise Refused("INVALID_REPLICA_ID")
        if self.generation < 0: raise Refused("INVALID_GENERATION")
        for value in (self.policy_digest, self.frontier_digest):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value): raise Refused("INVALID_DIGEST")

    @property
    def digest(self) -> str:
        body={"clock":self.clock.values,"frontier":self.frontier_digest,"generation":self.generation,"policy":self.policy_digest,"replica":self.replica_id,"subject":self.subject.identity}
        return sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
