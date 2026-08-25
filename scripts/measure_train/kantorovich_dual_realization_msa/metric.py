from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class GroundMetric:
    cost: tuple[tuple[Fraction, ...], ...]
    def __post_init__(self):
        n=len(self.cost)
        if n==0 or any(len(r)!=n for r in self.cost): raise Refused("REFUSED[INVALID_METRIC_SHAPE]")
        for i in range(n):
            if self.cost[i][i]!=0: raise Refused("REFUSED[NONZERO_DIAGONAL]")
            for j in range(n):
                if self.cost[i][j]<0 or self.cost[i][j]!=self.cost[j][i]: raise Refused("REFUSED[INVALID_METRIC]")
                for k in range(n):
                    if self.cost[i][k] > self.cost[i][j] + self.cost[j][k]: raise Refused("REFUSED[TRIANGLE_VIOLATION]")
