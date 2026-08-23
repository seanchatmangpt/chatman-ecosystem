from dataclasses import dataclass
from fractions import Fraction
from .policy import RobustStrategy
from .sensitivity import Interval
from .refusal import refuse

@dataclass(frozen=True)
class Candidate:
    policy_digest: str
    interval: Interval
    breakdown: Fraction

def dominates(a,b):
    aw,bw=a.interval.width,b.interval.width
    ge=a.interval.lower>=b.interval.lower and aw<=bw and a.breakdown>=b.breakdown
    strict=a.interval.lower>b.interval.lower or aw<bw or a.breakdown>b.breakdown
    return ge and strict

def pareto(items):
    xs=tuple(items); return tuple(x for x in xs if not any(dominates(y,x) for y in xs if y is not x))

def select(items,strategy:RobustStrategy,current_digest:str):
    xs=pareto(items)
    if not xs: refuse("NO_ROBUST_CANDIDATE")
    if strategy is RobustStrategy.HOLD:
        for x in xs:
            if x.policy_digest==current_digest: return x
        refuse("CURRENT_POLICY_NOT_ROBUST")
    if strategy is RobustStrategy.MAX_LOWER: return max(xs,key=lambda x:(x.interval.lower,-x.interval.width,x.policy_digest))
    if strategy is RobustStrategy.MIN_WIDTH: return min(xs,key=lambda x:(x.interval.width,-x.interval.lower,x.policy_digest))
    if strategy is RobustStrategy.MAX_BREAKDOWN: return max(xs,key=lambda x:(x.breakdown,x.interval.lower,x.policy_digest))
    refuse("UNKNOWN_ROBUST_STRATEGY")
