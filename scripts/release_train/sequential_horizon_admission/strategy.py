from dataclasses import dataclass
from fractions import Fraction
from enum import StrEnum
from .rational import nonnegative
class Strategy(StrEnum):
    MAX_INFORMATION="MAX_INFORMATION"; INFORMATION_PER_COST="INFORMATION_PER_COST"; MAX_INDEPENDENCE="MAX_INDEPENDENCE"; UCB_DISCOVERY="UCB_DISCOVERY"; MINIMAX_LATENCY="MINIMAX_LATENCY"
@dataclass(frozen=True)
class Candidate:
    name:str; information:Fraction; independence:Fraction; cost:Fraction; latency:Fraction; uncertainty:Fraction
    def __post_init__(self):
        for n in ("information","independence","cost","latency","uncertainty"): object.__setattr__(self,n,nonnegative(getattr(self,n)))
def select(candidates,strategy):
    xs=tuple(candidates)
    if not xs: return None
    if strategy is Strategy.MAX_INFORMATION: return max(xs,key=lambda x:(x.information,x.name))
    if strategy is Strategy.INFORMATION_PER_COST: return max(xs,key=lambda x:(x.information/(x.cost or Fraction(1,10**9)),x.name))
    if strategy is Strategy.MAX_INDEPENDENCE: return max(xs,key=lambda x:(x.independence,x.name))
    if strategy is Strategy.UCB_DISCOVERY: return max(xs,key=lambda x:(x.information+x.uncertainty,x.name))
    return min(xs,key=lambda x:(x.latency,x.name))
