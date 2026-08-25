from dataclasses import dataclass
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class PolicyState:
    subject: Subject
    generation: int
    revision: int
    digest: str
    payload_digest: str
    def __post_init__(self):
        if self.generation < 0 or self.revision < 0: raise Refused("REFUSED[INVALID_STATE_VERSION]")
        for value in (self.digest, self.payload_digest):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value): raise Refused("REFUSED[INVALID_STATE_DIGEST]")
