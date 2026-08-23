from dataclasses import dataclass
from fractions import Fraction
from .exact import positive
@dataclass(frozen=True)
class PageHinkley:
    threshold: Fraction
    delta: Fraction=Fraction(0)
    cumulative: Fraction=Fraction(0)
    minimum: Fraction=Fraction(0)
    drifted: bool=False
    @classmethod
    def start(cls, threshold=Fraction(1,2), delta=Fraction(1,100)):
        return cls(positive(threshold), Fraction(delta))
    def advance(self, residual):
        x=Fraction(residual)-self.delta
        c=self.cumulative+x
        m=min(self.minimum,c)
        d=(c-m)>self.threshold or self.drifted
        return PageHinkley(self.threshold,self.delta,c,m,d)
def detect(residuals, threshold=Fraction(1,2)):
    s=PageHinkley.start(threshold)
    for r in residuals: s=s.advance(r)
    return s
