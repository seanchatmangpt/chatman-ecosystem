from dataclasses import dataclass
from .subject import Refused, Subject

@dataclass(frozen=True, order=True)
class Certificate:
    subject: Subject
    generation: int
    digest: str

    def __post_init__(self):
        if self.generation < 0:
            raise Refused("REFUSED[INVALID_GENERATION]")
        if len(self.digest) != 64 or any(c not in "0123456789abcdef" for c in self.digest):
            raise Refused("REFUSED[INVALID_CERTIFICATE_DIGEST]")
