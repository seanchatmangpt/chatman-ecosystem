from fractions import Fraction
from .errors import Refused
def nonnegative(value,code="NEGATIVE_VALUE"):
    q=value if isinstance(value,Fraction) else Fraction(value)
    if q<0: raise Refused(code)
    return q
def unit(value,code="OUTSIDE_UNIT_INTERVAL"):
    q=value if isinstance(value,Fraction) else Fraction(value)
    if not 0<=q<=1: raise Refused(code)
    return q
