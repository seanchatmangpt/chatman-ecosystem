from dataclasses import dataclass
from .sensitivity import Interval
@dataclass(frozen=True, slots=True)
class CandidateInterval: policy_digest:str; interval:Interval; breakdown:object|None
def dominates(a,b): return a.interval.lower > b.interval.upper
def pareto(candidates):
    c=tuple(candidates)
    return tuple(x for x in c if not any(y is not x and y.interval.lower >= x.interval.lower and y.interval.width <= x.interval.width and (y.interval.lower > x.interval.lower or y.interval.width < x.interval.width) for y in c))
