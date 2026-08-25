from fractions import Fraction
from .errors import Refused

def unit(value, name="value"):
    q = value if isinstance(value, Fraction) else Fraction(value)
    if q < 0 or q > 1:
        raise Refused("OUT_OF_UNIT_INTERVAL", name)
    return q

def nonnegative(value, name="value"):
    q = value if isinstance(value, Fraction) else Fraction(value)
    if q < 0:
        raise Refused("NEGATIVE_VALUE", name)
    return q
