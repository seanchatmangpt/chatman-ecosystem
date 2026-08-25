from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class Cusum:
    threshold: Fraction
    drift: Fraction = Fraction(0,1)
    positive: Fraction = Fraction(0,1)

    def __post_init__(self):
        if self.threshold <= 0: raise Refused("NONPOSITIVE_THRESHOLD")

    def advance(self, x: Fraction) -> "Cusum":
        p=max(Fraction(0,1), self.positive + x - self.drift)
        return Cusum(self.threshold,self.drift,p)

    @property
    def changed(self) -> bool:
        return self.positive >= self.threshold
