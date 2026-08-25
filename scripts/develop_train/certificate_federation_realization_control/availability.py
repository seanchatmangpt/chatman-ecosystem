from dataclasses import dataclass
from math import sqrt
from statistics import NormalDist
from .errors import Refused
from .observation import TransportState

@dataclass(frozen=True)
class Wilson:
    support: int
    resolved: int
    lower: float
    upper: float

def wilson(observations, confidence=0.95) -> Wilson:
    values = tuple(observations)
    n = len(values)
    if n < 2 or not (0.5 < confidence < 1):
        raise Refused("INSUFFICIENT_AVAILABILITY_SUPPORT")
    successes = sum(o.state == TransportState.RESOLVED for o in values)
    p = successes/n
    z = NormalDist().inv_cdf((1+confidence)/2)
    denom = 1 + z*z/n
    centre = (p + z*z/(2*n))/denom
    radius = z*sqrt((p*(1-p)+z*z/(4*n))/n)/denom
    return Wilson(n, successes, max(0.0, centre-radius), min(1.0, centre+radius))
