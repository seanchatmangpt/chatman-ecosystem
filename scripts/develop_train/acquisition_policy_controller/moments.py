from dataclasses import dataclass
from math import sqrt
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class Moments:
    n:int=0
    mean:float=0.0
    m2:float=0.0
    def update(self,x):
        n=self.n+1; d=x-self.mean; mean=self.mean+d/n
        return Moments(n,mean,self.m2+d*(x-mean))
    @property
    def variance(self): return self.m2/(self.n-1) if self.n>1 else 0.0
    @property
    def stderr(self): return sqrt(self.variance/self.n) if self.n else 0.0
    def lower_confidence(self,z=1.96):
        if z<0: raise Refusal("REFUSED_INVALID_CONFIDENCE")
        return self.mean-z*self.stderr
