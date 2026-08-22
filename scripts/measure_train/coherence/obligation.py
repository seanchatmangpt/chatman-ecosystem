from dataclasses import dataclass
from enum import Enum
from .subject import Refusal

class Axis(str, Enum):
    FOCUSED="FOCUSED"; REPOSITORY="REPOSITORY"; RUNTIME="RUNTIME"; ARTIFACT="ARTIFACT"; DEPENDENCY="DEPENDENCY"; RECEIPT="RECEIPT"

class Requiredness(str, Enum): REQUIRED="REQUIRED"; OPTIONAL="OPTIONAL"

@dataclass(frozen=True, order=True)
class Obligation:
    obligation_id: str
    axis: Axis
    scope: str
    requiredness: Requiredness = Requiredness.REQUIRED
    def __post_init__(self):
        if not self.obligation_id or any(c.isspace() for c in self.obligation_id): raise Refusal("INVALID_OBLIGATION_ID")
        if not self.scope: raise Refusal("EMPTY_SCOPE")
