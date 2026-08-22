from dataclasses import dataclass
from math import log,sqrt
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class StrategyScore:
    strategy:str
    conservative:float
    exploration_bonus:float
    total:float
    admissible:bool
    reason:str
def score(e,total_n,policy):
    if e.utility.n<policy.min_support: return StrategyScore(e.strategy,float("-inf"),0,float("-inf"),False,"INSUFFICIENT_SUPPORT")
    if e.failure_rate>policy.max_failure_rate: return StrategyScore(e.strategy,float("-inf"),0,float("-inf"),False,"FAILURE_RATE")
    if e.cost.mean>policy.max_cost: return StrategyScore(e.strategy,float("-inf"),0,float("-inf"),False,"COST")
    if e.latency.mean>policy.max_latency_ms: return StrategyScore(e.strategy,float("-inf"),0,float("-inf"),False,"LATENCY")
    c=e.utility.lower_confidence(); b=policy.exploration*sqrt(log(max(2,total_n))/e.utility.n)
    return StrategyScore(e.strategy,c,b,c+b,True,"ADMITTED")
def select(scores):
    a=[s for s in scores if s.admissible]
    if not a: raise Refusal("REFUSED_NO_ADMISSIBLE_STRATEGY")
    return sorted(a,key=lambda s:(-s.total,s.strategy))[0]
