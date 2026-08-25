from dataclasses import dataclass
from fractions import Fraction
from .utility import PolicyBound
from .interval import Interval
from .refusal import Refused
@dataclass(frozen=True)
class Portfolio:
    members:tuple[PolicyBound,...]
    @property
    def digest_key(self): return tuple(sorted(m.policy.digest for m in self.members))
    def aggregate(self, weights:tuple[Fraction,...])->Interval:
        if len(weights)!=len(self.members) or sum(weights)!=1 or any(w<0 for w in weights): raise Refused('INVALID_PORTFOLIO_WEIGHTS')
        lo=sum(w*m.utility.lower for w,m in zip(weights,self.members)); hi=sum(w*m.utility.upper for w,m in zip(weights,self.members))
        return Interval(lo,hi)
    @property
    def cost(self): return sum((m.cost for m in self.members),Fraction(0))
    @property
    def latency(self): return max((m.latency for m in self.members), default=Fraction(0))
