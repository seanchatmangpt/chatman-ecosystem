from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class GroundMetric:
    labels:tuple; costs:tuple
    @classmethod
    def of(cls,labels,costs):
        labels=tuple(labels); n=len(labels)
        if n==0 or len(set(labels))!=n or len(costs)!=n or any(len(r)!=n for r in costs): raise Refused("INVALID_METRIC_SHAPE")
        c=tuple(tuple(Fraction(x) for x in r) for r in costs)
        for i in range(n):
            if c[i][i]!=0: raise Refused("NONZERO_DIAGONAL")
            for j in range(n):
                if c[i][j]<0 or c[i][j]!=c[j][i]: raise Refused("INVALID_METRIC_SYMMETRY")
                for k in range(n):
                    if c[i][k]>c[i][j]+c[j][k]: raise Refused("TRIANGLE_VIOLATION")
        return cls(labels,c)
    def cost(self,a,b):
        try: return self.costs[self.labels.index(a)][self.labels.index(b)]
        except ValueError: raise Refused("METRIC_SUPPORT_GAP")
