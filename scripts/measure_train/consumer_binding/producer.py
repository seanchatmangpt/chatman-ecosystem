from dataclasses import dataclass
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class ProducerEvidence:
    subject: Subject
    receipt_sha256: str
    schema: str
    standing: str

    def __post_init__(self):
        if len(self.receipt_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.receipt_sha256):
            raise Refused("REFUSED[INVALID_PRODUCER_RECEIPT]")
        if not self.schema.strip():
            raise Refused("REFUSED[EMPTY_PRODUCER_SCHEMA]")
        if self.standing not in {"UNKNOWN","PARTIAL_ALIVE","ALIVE","BLOCKED","BUILD_BROKEN","UNSUPPORTED"}:
            raise Refused("REFUSED[INVALID_PRODUCER_STANDING]")
