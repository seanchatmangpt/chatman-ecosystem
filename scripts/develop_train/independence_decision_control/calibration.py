from dataclasses import dataclass
from fractions import Fraction

from .errors import Refused


@dataclass(frozen=True)
class DecisionCalibration:
    generation: int
    digest: str
    support: int
    false_independent: Fraction
    false_dependent: Fraction
    defer_rate: Fraction

    def __post_init__(self):
        if self.generation < 0 or self.support < 0 or len(self.digest) != 64:
            raise Refused("INVALID_CALIBRATION")
        for value in (self.false_independent, self.false_dependent, self.defer_rate):
            if value < 0 or value > 1:
                raise Refused("INVALID_CALIBRATION")

    def admitted(self, min_support=20, max_false_independent=Fraction(1, 10), max_false_dependent=Fraction(1, 5)):
        return self.support >= min_support and self.false_independent <= max_false_independent and self.false_dependent <= max_false_dependent


def current(items):
    if not items:
        raise Refused("NO_CALIBRATION")
    generation = max(item.generation for item in items)
    latest = [item for item in items if item.generation == generation]
    if len({item.digest for item in latest}) != 1:
        raise Refused("SPLIT_CURRENT_CALIBRATION")
    return latest[0]
