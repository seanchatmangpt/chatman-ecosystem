import hashlib, json
from dataclasses import dataclass
from .errors import Refused
from .vector_clock import VectorClock

@dataclass(frozen=True)
class ReplicaState:
    replica: str
    subject: str
    generation: int
    value_digest: str
    clock: VectorClock

    def __post_init__(self):
        if not self.replica or self.generation < 0 or len(self.value_digest) != 64:
            raise Refused("INVALID_REPLICA_STATE")

    def digest(self) -> str:
        body={"replica":self.replica,"subject":self.subject,"generation":self.generation,"value_digest":self.value_digest,"clock":self.clock.entries}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
