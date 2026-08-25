import re
from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True, order=True)
class TransportIdentity:
    name: str
    generation: int
    implementation_digest: str
    model_digest: str
    domain: str

    def __post_init__(self):
        if not self.name.strip() or not self.domain.strip():
            raise Refused("REFUSED[EMPTY_TRANSPORT_IDENTITY]")
        if self.generation < 0:
            raise Refused("REFUSED[INVALID_TRANSPORT_GENERATION]")
        for value in (self.implementation_digest, self.model_digest):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise Refused("REFUSED[INVALID_TRANSPORT_DIGEST]")
