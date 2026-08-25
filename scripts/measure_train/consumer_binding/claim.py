from dataclasses import dataclass
from .consumer import Consumer
from .producer import ProducerEvidence
from .lease import EvidenceLease
from .subject import Refused

@dataclass(frozen=True, order=True)
class ConsumptionClaim:
    consumer: Consumer
    producer: ProducerEvidence
    lease: EvidenceLease
    required_scope: str

    def __post_init__(self):
        if self.required_scope not in {"FOCUSED","REPOSITORY","RUNTIME","ARTIFACT","DEPENDENCY","RECEIPT"}:
            raise Refused("REFUSED[INVALID_REQUIRED_SCOPE]")
