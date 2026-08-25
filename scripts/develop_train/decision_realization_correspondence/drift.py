from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Cusum:
    value: Fraction=Fraction()
    threshold: Fraction=Fraction(1,2)
    slack: Fraction=Fraction()
    def update(self, realized: Fraction, expected: Fraction):
        nxt=max(Fraction(), self.value + realized-expected-self.slack)
        return Cusum(nxt,self.threshold,self.slack)
    @property
    def changed(self):
        return self.value >= self.threshold
