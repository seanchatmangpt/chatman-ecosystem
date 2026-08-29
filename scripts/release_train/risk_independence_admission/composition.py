from dataclasses import dataclass
from .probability import unit
from .decision import Decision
from .errors import Refused

@dataclass(frozen=True)
class Interval:
    low:object; high:object
    def __post_init__(self):
        object.__setattr__(self,'low',unit(self.low)); object.__setattr__(self,'high',unit(self.high))
        if self.low>self.high: raise Refused('INVALID_INTERVAL')
def conservative(a,b): return Interval(max(0,a.low+b.low-1),min(a.high,b.high))
def independent(a,b): return Interval(a.low*b.low,a.high*b.high)
def compose(a,b,decision):
    if decision==Decision.INDEPENDENT: return independent(a,b)
    if decision==Decision.DEPENDENT: return conservative(a,b)
    raise Refused('INDEPENDENCE_DECISION_DEFERRED')
