from dataclasses import dataclass
from math import sqrt
from .errors import Refused
from .observation import TransportState

@dataclass(frozen=True)
class Correlation:
    phi: float
    paired: int

def phi(left, right) -> Correlation:
    if len(left) != len(right) or len(left) < 2:
        raise Refused("INSUFFICIENT_CORRELATION_SUPPORT")
    a=b=c=d=0
    for x,y in zip(left,right):
        xf = x.state != TransportState.RESOLVED
        yf = y.state != TransportState.RESOLVED
        if xf and yf: a += 1
        elif xf and not yf: b += 1
        elif not xf and yf: c += 1
        else: d += 1
    denom = sqrt((a+b)*(c+d)*(a+c)*(b+d))
    value = ((a*d - b*c) / denom) if denom else 0.0
    return Correlation(value, len(left))

def require_independent(correlation: Correlation, max_abs_phi: float = 0.2):
    if abs(correlation.phi) > max_abs_phi:
        raise Refused("CORRELATED_TRANSPORT_FAILURES")
    return correlation
