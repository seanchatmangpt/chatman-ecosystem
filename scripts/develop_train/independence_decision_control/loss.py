from dataclasses import dataclass
from fractions import Fraction

from .errors import Refused


@dataclass(frozen=True)
class LossMatrix:
    false_independent: Fraction
    false_dependent: Fraction
    defer: Fraction

    def __post_init__(self):
        if min(self.false_independent, self.false_dependent, self.defer) < 0:
            raise Refused("INVALID_LOSS")
