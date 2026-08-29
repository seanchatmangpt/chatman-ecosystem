from dataclasses import dataclass
from .subject import Subject
from .lease import EvidenceLease
@dataclass(frozen=True)
class ConsumptionClaim:
    consumer:Subject
    producer:Subject
    component:str
    receipt:str
    schema:str
    required_scope:str
    lease:EvidenceLease
    def __post_init__(self):
        if not self.component.strip(): raise ValueError("REFUSED[ANONYMOUS_CONSUMER]")
        if self.required_scope not in {"FOCUSED","INTEGRATION","REPOSITORY"}:
            raise ValueError("REFUSED[INVALID_REQUIRED_SCOPE]")
