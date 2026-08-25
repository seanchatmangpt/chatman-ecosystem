from dataclasses import dataclass
from fractions import Fraction
from .probability import normalized
from .refusals import Refused

@dataclass(frozen=True)
class BeliefState:
    generation: int
    probabilities: dict[str, Fraction]

    def __post_init__(self):
        if self.generation < 0:
            raise Refused("REFUSED_INVALID_BELIEF_GENERATION")
        object.__setattr__(self, "probabilities", normalized(self.probabilities))

    @property
    def confidence(self) -> Fraction:
        return max(self.probabilities.values())
