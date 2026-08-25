from dataclasses import dataclass
from fractions import Fraction
from .relation import Relation
from .refusal import Refused

@dataclass(frozen=True)
class CalibrationEvidence:
    relation: Relation
    generation: int
    support: int
    false_equivalence: int
    false_refusal: int
    evaluation_cost: Fraction

    def __post_init__(self):
        if self.generation < 0:
            raise Refused("REFUSED[NEGATIVE_GENERATION]")
        if self.support <= 0:
            raise Refused("REFUSED[EMPTY_CALIBRATION_SUPPORT]")
        if not (0 <= self.false_equivalence <= self.support):
            raise Refused("REFUSED[INVALID_FALSE_EQUIVALENCE_COUNT]")
        if not (0 <= self.false_refusal <= self.support):
            raise Refused("REFUSED[INVALID_FALSE_REFUSAL_COUNT]")
        if self.evaluation_cost < 0:
            raise Refused("REFUSED[NEGATIVE_EVALUATION_COST]")

    @property
    def fe_rate(self) -> Fraction:
        return Fraction(self.false_equivalence, self.support)

    @property
    def fr_rate(self) -> Fraction:
        return Fraction(self.false_refusal, self.support)
