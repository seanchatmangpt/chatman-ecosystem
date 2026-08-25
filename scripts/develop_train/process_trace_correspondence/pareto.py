from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate:
    name:str; strength:int; coverage:float; independence:float; divergence:float; cost:float
def dominates(a,b):
    good=(a.strength>=b.strength and a.coverage>=b.coverage and a.independence>=b.independence and a.divergence<=b.divergence and a.cost<=b.cost)
    strict=(a.strength>b.strength or a.coverage>b.coverage or a.independence>b.independence or a.divergence<b.divergence or a.cost<b.cost)
    return good and strict
def frontier(xs): return tuple(sorted((x for x in xs if not any(dominates(y,x) for y in xs if y!=x)),key=lambda z:z.name))
