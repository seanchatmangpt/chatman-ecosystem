from dataclasses import dataclass
from .moments import Moments
from .realization import STRATEGIES
from .utility import utility
@dataclass(frozen=True, slots=True)
class StrategyEvidence:
    strategy:str
    utility:Moments
    failures:int
    cost:Moments
    latency:Moments
    @property
    def failure_rate(self): return self.failures/self.utility.n if self.utility.n else 0.0
def aggregate(rows):
    acc={s:StrategyEvidence(s,Moments(),0,Moments(),Moments()) for s in STRATEGIES}
    for r in rows:
        e=acc[r.strategy]
        acc[r.strategy]=StrategyEvidence(r.strategy,e.utility.update(utility(r).score),e.failures+(r.outcome=="FAIL"),e.cost.update(r.actual_cost),e.latency.update(r.actual_latency_ms))
    return acc
