from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class PageHinkley:
    mean: Fraction = Fraction()
    cumulative: Fraction = Fraction()
    minimum: Fraction = Fraction()
    count: int = 0

    def advance(self, value: Fraction, *, delta=Fraction(1,100)):
        n=self.count+1
        mean=self.mean + (value-self.mean)/n
        cumulative=self.cumulative + value - mean - delta
        minimum=min(self.minimum, cumulative)
        return PageHinkley(mean, cumulative, minimum, n)

    def drifted(self, *, threshold=Fraction(1,2)):
        return self.count >= 3 and self.cumulative-self.minimum > threshold

def from_residuals(values):
    state=PageHinkley()
    for value in values:
        state=state.advance(value)
    return state
