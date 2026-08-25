from fractions import Fraction
from .errors import Refused

def exact(value) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    raise Refused("REFUSED_INEXACT_NUMERIC_DOMAIN")

def nonnegative(value) -> Fraction:
    out = exact(value)
    if out < 0:
        raise Refused("REFUSED_NEGATIVE_VALUE")
    return out

def unit(value) -> Fraction:
    out = exact(value)
    if not 0 <= out <= 1:
        raise Refused("REFUSED_OUTSIDE_UNIT_INTERVAL")
    return out
