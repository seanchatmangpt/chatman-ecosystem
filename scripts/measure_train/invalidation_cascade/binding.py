from dataclasses import dataclass
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class Binding:
    consumer: Subject
    producer: Subject
    producer_receipt: str
    schema: str
    scope: str
    binding_id: str
    def __post_init__(self):
        if len(self.producer_receipt) != 64 or any(c not in "0123456789abcdef" for c in self.producer_receipt):
            raise Refused("REFUSED[INVALID_PRODUCER_RECEIPT]")
        if not self.schema.strip() or not self.binding_id.strip():
            raise Refused("REFUSED[INVALID_BINDING]")
        if self.scope not in {"FOCUSED","RUNTIME","ARTIFACT","DEPENDENCY","REPOSITORY"}:
            raise Refused("REFUSED[INVALID_SCOPE]")
