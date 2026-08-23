from dataclasses import dataclass
from enum import IntEnum
from fractions import Fraction
from .refusal import Refused

class State(IntEnum):
    PASS = 0
    UNSUPPORTED = 1
    UNKNOWN = 2
    REFUSED = 3
    BLOCKED = 4
    FAIL = 5

@dataclass(frozen=True)
class Obligation:
    key: str
    state: State
    weight: Fraction = Fraction(1, 1)

    def __post_init__(self):
        if not self.key:
            raise Refused("EMPTY_OBLIGATION")
        if self.weight <= 0:
            raise Refused("NONPOSITIVE_WEIGHT", self.key)
