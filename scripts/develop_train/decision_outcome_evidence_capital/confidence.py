from dataclasses import dataclass
from math import log, sqrt
from .errors import Refused

@dataclass(frozen=True)
class Bound:
    mean: float
    radius: float
    lower: float
    upper: float
    n: int

def empirical_bernstein(values, delta=0.05, value_range=1.0):
    xs = tuple(float(x) for x in values)
    n = len(xs)
    if n < 2:
        raise Refused("INSUFFICIENT_CONFIDENCE_SUPPORT")
    if not (0 < delta < 1) or value_range <= 0:
        raise Refused("INVALID_CONFIDENCE_PARAMETERS")
    mean = sum(xs)/n
    var = sum((x-mean)**2 for x in xs)/(n-1)
    radius = sqrt(2*var*log(3/delta)/n) + 3*value_range*log(3/delta)/n
    return Bound(mean, radius, mean-radius, mean+radius, n)
