from fractions import Fraction
from .distribution import Distribution
from .refusal import Refused
def tv_extremes(reference,radius):
    if len(reference.support)!=2: raise Refused("UNSUPPORTED_ADVERSARY_DIMENSION")
    r=Fraction(radius); a,b=sorted(reference.support); m=reference.mapping(); p=m[a]
    lo=max(Fraction(),p-r); hi=min(Fraction(1),p+r)
    return tuple(Distribution.from_mapping({a:x,b:1-x}) for x in sorted({lo,p,hi}))
