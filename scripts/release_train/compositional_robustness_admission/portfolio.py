from dataclasses import dataclass
from fractions import Fraction
from .policy_bound import PolicyBound
from .intervals import Interval
from .refusal import Refused

@dataclass(frozen=True)
class Portfolio:
    members: tuple[PolicyBound, ...]
    weights: tuple[Fraction, ...]
    def __post_init__(self):
        if len(self.members) != len(self.weights) or not self.members or any(w < 0 for w in self.weights) or sum(self.weights) != 1:
            raise Refused("INVALID_PORTFOLIO_WEIGHTS")
    @property
    def interval(self):
        return Interval(sum(w*m.interval.lower for w,m in zip(self.weights,self.members)), sum(w*m.interval.upper for w,m in zip(self.weights,self.members)))
    @property
    def cost(self): return sum(w*m.cost for w,m in zip(self.weights,self.members))
    @property
    def latency(self): return max(m.latency for m in self.members)
    @property
    def breakdown_gamma(self): return min(m.breakdown_gamma for m in self.members)
    @property
    def digests(self): return tuple(sorted(m.policy.digest for m in self.members))
