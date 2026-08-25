from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate:
    name:str; uncertainty:float; regret:float; cost:float; blocker_relief:float

def dominates(a,b):
    better=(a.uncertainty<=b.uncertainty and a.regret<=b.regret and a.cost<=b.cost and a.blocker_relief>=b.blocker_relief)
    strict=(a.uncertainty<b.uncertainty or a.regret<b.regret or a.cost<b.cost or a.blocker_relief>b.blocker_relief)
    return better and strict

def frontier(cs):
    cs=tuple(cs)
    return tuple(c for c in cs if not any(dominates(o,c) for o in cs if o!=c))
