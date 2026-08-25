from dataclasses import dataclass
from fractions import Fraction


@dataclass
class CUSUM:
    threshold: Fraction
    slack: Fraction = Fraction(0)
    value: Fraction = Fraction(0)

    def update(self, residual: Fraction):
        self.value = max(Fraction(0), self.value + residual - self.slack)
        return self.value >= self.threshold
