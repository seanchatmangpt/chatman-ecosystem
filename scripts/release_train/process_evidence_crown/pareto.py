from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Candidate:
    id:str; uncertainty:Fraction; regret:Fraction; cost:Fraction; blocker_relief:Fraction

def dominates(a,b):
    weak=(a.uncertainty<=b.uncertainty and a.regret<=b.regret and a.cost<=b.cost and a.blocker_relief>=b.blocker_relief)
    strict=(a.uncertainty<b.uncertainty or a.regret<b.regret or a.cost<b.cost or a.blocker_relief>b.blocker_relief)
    return weak and strict

def frontier(items):
    return tuple(sorted((x for x in items if not any(dominates(y,x) for y in items if y!=x)),key=lambda x:x.id))
