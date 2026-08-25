from fractions import Fraction
from .refusal import Refused
def empirical_radius(distances,quantile=Fraction(19,20)):
    vals=sorted(Fraction(x) for x in distances)
    if not vals: raise Refused("REFUSED[NO_RADIUS_EVIDENCE]")
    if quantile<=0 or quantile>1: raise Refused("REFUSED[INVALID_RADIUS_QUANTILE]")
    rank=max(1,(quantile.numerator*len(vals)+quantile.denominator-1)//quantile.denominator)
    return vals[min(rank-1,len(vals)-1)]
def radius_miss_rate(distances,radius):
    vals=tuple(Fraction(x) for x in distances)
    return Fraction(0) if not vals else Fraction(sum(1 for x in vals if x>radius),len(vals))
