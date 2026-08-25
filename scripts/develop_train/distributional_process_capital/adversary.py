from fractions import Fraction
from .distribution import Distribution
from .errors import Refused

def tv_extremes(center,radius):
    r=Fraction(radius)
    if r<0 or r>1:
        raise Refused("INVALID_TV_RADIUS")
    keys=sorted(center.support)
    if len(keys)!=2:
        raise Refused("TV_ADVERSARY_REQUIRES_TWO_SUPPORT")
    a,b=keys
    pa=center.get(a)
    low=max(Fraction(0),pa-r)
    high=min(Fraction(1),pa+r)
    return tuple({d.mass:d for d in (Distribution.from_mapping({a:low,b:1-low}),Distribution.from_mapping({a:high,b:1-high}))}.values())
