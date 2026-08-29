from dataclasses import dataclass
from math import sqrt

@dataclass(frozen=True)
class Moments:
    n: int=0
    mean: float=0.0
    m2: float=0.0
    def add(self, x: float):
        n=self.n+1
        delta=x-self.mean
        mean=self.mean+delta/n
        return Moments(n, mean, self.m2+delta*(x-mean))
    @property
    def variance(self):
        return self.m2/(self.n-1) if self.n>1 else 0.0
    def lower_confidence(self, z: float=1.0):
        return self.mean-z*sqrt(self.variance/self.n) if self.n else float("-inf")
