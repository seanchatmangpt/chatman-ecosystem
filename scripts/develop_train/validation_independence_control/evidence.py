from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    generation: int
    parents: tuple[str,...]=()
    cost: Fraction=Fraction(0)
    def __post_init__(self):
        if not self.evidence_id or self.generation < 0 or self.cost < 0:
            raise Refused("INVALID_EVIDENCE")
        if self.evidence_id in self.parents:
            raise Refused("SELF_PARENT")
