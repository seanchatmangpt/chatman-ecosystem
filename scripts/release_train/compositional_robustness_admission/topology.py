from enum import Enum
from .intervals import Interval

class Topology(str, Enum):
    DOMINANT = "DOMINANT"
    OVERLAP = "OVERLAP"
    INCOMPARABLE = "INCOMPARABLE"

def classify(a: Interval, b: Interval) -> Topology:
    if a.lower >= b.upper or b.lower >= a.upper: return Topology.DOMINANT
    if a.intersects(b): return Topology.OVERLAP
    return Topology.INCOMPARABLE
