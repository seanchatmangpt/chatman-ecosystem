from dataclasses import dataclass
from .subject import Subject, Refusal

@dataclass(frozen=True)
class PromotionBinding:
    consumer: Subject
    producer: Subject
    receipt: str
    schema: str
    scope: str
    binding_id: str
    def __post_init__(self):
        if len(self.receipt) != 64 or any(c not in '0123456789abcdef' for c in self.receipt):
            raise Refusal('REFUSED[INVALID_RECEIPT]')
        if not self.schema or not self.scope or not self.binding_id:
            raise Refusal('REFUSED[INCOMPLETE_BINDING]')
