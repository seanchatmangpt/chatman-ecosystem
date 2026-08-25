from dataclasses import dataclass
from fractions import Fraction

@dataclass
class Cusum:
    threshold: Fraction
    slack: Fraction = Fraction(0)
    value: Fraction = Fraction(0)
    def update(self, residual):
        self.value=max(Fraction(0), self.value + Fraction(residual)-self.slack)
        return self.value >= self.threshold
