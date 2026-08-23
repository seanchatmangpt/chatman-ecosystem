from fractions import Fraction
from .errors import Refused
def unit(value, *, code="INVALID_UNIT"):
    q=Fraction(value)
    if q < 0 or q > 1: raise Refused(code, str(value))
    return q
def nonnegative(value, *, code="NEGATIVE_VALUE"):
    q=Fraction(value)
    if q < 0: raise Refused(code, str(value))
    return q
def positive(value, *, code="NONPOSITIVE_VALUE"):
    q=Fraction(value)
    if q <= 0: raise Refused(code, str(value))
    return q
