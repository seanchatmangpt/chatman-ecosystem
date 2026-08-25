from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Candidate:
    name:str
    nominal:Fraction
    worst:Fraction
    radius:Fraction
    support:int

def dominates(a,b):
    av=(a.nominal,a.worst,a.radius,-a.support)
    bv=(b.nominal,b.worst,b.radius,-b.support)
    return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))

def frontier(candidates):
    cs=tuple(candidates)
    return tuple(sorted((c for c in cs if not any(o!=c and dominates(o,c) for o in cs)),key=lambda c:c.name))
