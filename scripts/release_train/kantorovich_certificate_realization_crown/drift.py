from dataclasses import dataclass
from fractions import Fraction
@dataclass
class Cusum:
    threshold: Fraction
    slack: Fraction = Fraction(0)
    state: Fraction = Fraction(0)
    def update(self, value: Fraction, target: Fraction):
        self.state=max(Fraction(0), self.state + value - target - self.slack)
        return self.state >= self.threshold
