from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Cusum:
    value: Fraction = Fraction(0,1)
    threshold: Fraction = Fraction(1,5)
    slack: Fraction = Fraction(0,1)

    def update(self, residual: Fraction) -> "Cusum":
        next_value = max(Fraction(0,1), self.value + abs(residual) - self.slack)
        return Cusum(next_value, self.threshold, self.slack)

    @property
    def changed(self) -> bool:
        return self.value >= self.threshold
