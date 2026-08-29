from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Belief:
    defect: Fraction
    generation: int

    def __post_init__(self):
        if not (Fraction(0) < self.defect < Fraction(1)):
            raise ValueError("REFUSED[INVALID_BELIEF_MASS]")
        if self.generation < 0:
            raise ValueError("REFUSED[INVALID_BELIEF_GENERATION]")
