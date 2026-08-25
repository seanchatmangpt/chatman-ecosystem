from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class FiniteMeasure:
    mass: tuple[Fraction, ...]
    def __post_init__(self):
        if not self.mass or any(x < 0 for x in self.mass) or sum(self.mass) != 1: raise Refused("REFUSED[INVALID_MEASURE]")
