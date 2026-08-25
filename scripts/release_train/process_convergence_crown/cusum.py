from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Cusum:
    positive: Fraction = Fraction(0,1)
    negative: Fraction = Fraction(0,1)
    threshold: Fraction = Fraction(2,1)
    drift: Fraction = Fraction(0,1)
    def advance(self, residual: Fraction):
        p=max(Fraction(0,1), self.positive + residual - self.drift)
        n=max(Fraction(0,1), self.negative - residual - self.drift)
        return Cusum(p,n,self.threshold,self.drift)
    @property
    def changed(self): return self.positive > self.threshold or self.negative > self.threshold
