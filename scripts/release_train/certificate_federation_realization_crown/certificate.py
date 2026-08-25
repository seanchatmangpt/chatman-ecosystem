from dataclasses import dataclass
from .refusal import Refused
from .subject import Subject

@dataclass(frozen=True)
class Certificate:
    subject: Subject
    generation: int
    semantic_digest: str
    certificate_digest: str

    def __post_init__(self) -> None:
        if self.generation < 0:
            raise Refused("INVALID_CERTIFICATE_GENERATION")
        for name, value in (("semantic", self.semantic_digest), ("certificate", self.certificate_digest)):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise Refused("INVALID_DIGEST", name)
