from math import sqrt
from .refusal import Refused

def phi(a: list[bool], b: list[bool]) -> float:
    if len(a) != len(b) or len(a) < 4:
        raise Refused("INSUFFICIENT_CORRELATION_SUPPORT")
    n11=sum(x and y for x,y in zip(a,b)); n10=sum(x and not y for x,y in zip(a,b))
    n01=sum((not x) and y for x,y in zip(a,b)); n00=sum((not x) and (not y) for x,y in zip(a,b))
    den=sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))
    return 0.0 if den == 0 else (n11*n00-n10*n01)/den

def require_independent(a: list[bool], b: list[bool], max_abs_phi: float=0.5) -> float:
    value=phi(a,b)
    if abs(value) > max_abs_phi:
        raise Refused("CORRELATED_TRANSPORT_FAILURES", f"{value:.6f}")
    return value
