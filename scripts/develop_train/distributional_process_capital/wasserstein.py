from fractions import Fraction
from .errors import Refused

def wasserstein1(p,q,ground_cost):
    keys=sorted(p.support|q.support)
    if len(keys)>2:
        raise Refused("WASSERSTEIN_DIMENSION_UNSUPPORTED",str(len(keys)))
    if len(keys)<=1:
        return Fraction(0)
    a,b=keys
    pair=(a,b) if (a,b) in ground_cost else (b,a)
    if pair not in ground_cost:
        raise Refused("GROUND_COST_MISSING",f"{a},{b}")
    cost=Fraction(ground_cost[pair])
    if cost<0:
        raise Refused("NEGATIVE_GROUND_COST")
    return abs(p.get(a)-q.get(a))*cost
