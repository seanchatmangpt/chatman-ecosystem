import math
from .errors import Refused

def normalize_distribution(values):
    vals=tuple(float(v) for v in values)
    if not vals or any(v < 0 for v in vals):
        raise Refused("INVALID_ERROR_DISTRIBUTION")
    total=sum(vals)
    if total <= 0:
        raise Refused("ZERO_ERROR_DISTRIBUTION")
    return tuple(v/total for v in vals)

def _kl(p, q):
    return sum(a * math.log2(a/b) for a,b in zip(p,q) if a > 0 and b > 0)

def jensen_shannon(left, right):
    p=normalize_distribution(left); q=normalize_distribution(right)
    if len(p) != len(q):
        raise Refused("DISTRIBUTION_DIMENSION_MISMATCH")
    m=tuple((a+b)/2 for a,b in zip(p,q))
    return (_kl(p,m)+_kl(q,m))/2
