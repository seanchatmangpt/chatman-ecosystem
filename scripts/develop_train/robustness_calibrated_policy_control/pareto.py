from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Candidate:
    key:tuple[str,...]
    lower:Fraction
    width:Fraction
    breakdown:Fraction
    cost:Fraction
    latency:Fraction
def dominates(a:Candidate,b:Candidate)->bool:
    better=(a.lower>=b.lower and a.width<=b.width and a.breakdown>=b.breakdown and a.cost<=b.cost and a.latency<=b.latency)
    strict=(a.lower>b.lower or a.width<b.width or a.breakdown>b.breakdown or a.cost<b.cost or a.latency<b.latency)
    return better and strict
def frontier(items:tuple[Candidate,...])->tuple[Candidate,...]:
    return tuple(sorted((x for x in items if not any(dominates(y,x) for y in items if y!=x)),key=lambda x:x.key))
