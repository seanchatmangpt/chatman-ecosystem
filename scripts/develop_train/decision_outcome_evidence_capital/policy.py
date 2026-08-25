from dataclasses import dataclass
from enum import Enum
import re
from .errors import Refused

_HEX = re.compile(r"^[0-9a-f]{64}$")

class Decision(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    DEPENDENT = "DEPENDENT"
    DEFER = "DEFER"

@dataclass(frozen=True)
class LossMatrix:
    false_independent: float
    false_dependent: float
    defer: float

    def __post_init__(self):
        if min(self.false_independent, self.false_dependent, self.defer) < 0:
            raise Refused("NEGATIVE_LOSS")

@dataclass(frozen=True)
class Policy:
    policy_id: str
    generation: int
    digest: str
    loss: LossMatrix

    def __post_init__(self):
        if not self.policy_id or self.generation < 0 or not _HEX.fullmatch(self.digest):
            raise Refused("INVALID_POLICY_IDENTITY")
