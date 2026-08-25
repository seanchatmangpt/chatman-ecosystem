from enum import Enum
from .utility import PolicyBound
class Topology(str,Enum):
    DOMINANT='DOMINANT'; OVERLAP='OVERLAP'; INCOMPARABLE='INCOMPARABLE'
def classify(bounds:tuple[PolicyBound,...])->Topology:
    if len(bounds)<2: return Topology.DOMINANT
    ordered=sorted(bounds,key=lambda b:(b.utility.lower,b.utility.upper), reverse=True)
    best=ordered[0]
    if all(best.utility.lower>o.utility.upper for o in ordered[1:]): return Topology.DOMINANT
    if any(best.utility.intersect(o.utility) for o in ordered[1:]): return Topology.OVERLAP
    return Topology.INCOMPARABLE
