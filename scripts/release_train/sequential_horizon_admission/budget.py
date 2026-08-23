from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .rational import nonnegative
@dataclass(frozen=True)
class Budget:
    cost:Fraction; latency:Fraction; samples:int
    def __post_init__(self):
        object.__setattr__(self,"cost",nonnegative(self.cost,"NEGATIVE_COST")); object.__setattr__(self,"latency",nonnegative(self.latency,"NEGATIVE_LATENCY"))
        if self.samples<0: raise Refused("NEGATIVE_SAMPLES")
    def consume(self,*,cost,latency,samples=1):
        c,l=nonnegative(cost),nonnegative(latency)
        if c>self.cost or l>self.latency or samples>self.samples: raise Refused("BUDGET_EXHAUSTED")
        return Budget(self.cost-c,self.latency-l,self.samples-samples)
