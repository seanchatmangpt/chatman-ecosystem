from fractions import Fraction
from .errors import Refused
def frac(v, *, code="INVALID_RATIONAL"):
    try: x=v if isinstance(v,Fraction) else Fraction(str(v))
    except Exception as e: raise Refused(code) from e
    return x
def unit(v):
    x=frac(v)
    if x < 0 or x > 1: raise Refused("OUT_OF_UNIT_INTERVAL")
    return x
def nonnegative(v):
    x=frac(v)
    if x < 0: raise Refused("NEGATIVE_VALUE")
    return x
def positive(v):
    x=frac(v)
    if x <= 0: raise Refused("NONPOSITIVE_VALUE")
    return x
