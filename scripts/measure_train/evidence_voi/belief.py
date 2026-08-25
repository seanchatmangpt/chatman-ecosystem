from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused

@dataclass(frozen=True, order=True)
class BeliefState:
    p_alive: Fraction
    generation: int
    def __post_init__(self):
        if not isinstance(self.p_alive, Fraction) or self.p_alive < 0 or self.p_alive > 1:
            raise Refused("REFUSED[INVALID_BELIEF]")
        if self.generation < 0:
            raise Refused("REFUSED[INVALID_BELIEF_GENERATION]")
    @property
    def p_not_alive(self):
        return 1 - self.p_alive
