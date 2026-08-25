from fractions import Fraction
from math import log2
from .subject import Refused

def binary_entropy(p: Fraction) -> float:
    if not (Fraction(0) <= p <= Fraction(1)):
        raise Refused("REFUSED[INVALID_BELIEF]")
    x=float(p)
    if x in (0.0,1.0):
        return 0.0
    return -(x*log2(x)+(1-x)*log2(1-x))

def entropy_reduction(prior: Fraction, posterior: Fraction) -> float:
    return binary_entropy(prior)-binary_entropy(posterior)
