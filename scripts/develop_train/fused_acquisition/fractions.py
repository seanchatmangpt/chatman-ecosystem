from fractions import Fraction
from .refusals import Refused

def unit(value, name: str) -> Fraction:
    q = value if isinstance(value, Fraction) else Fraction(value)
    if q < 0 or q > 1:
        raise Refused("OUT_OF_UNIT_INTERVAL", name)
    return q

def positive(value, name: str) -> Fraction:
    q = value if isinstance(value, Fraction) else Fraction(value)
    if q <= 0:
        raise Refused("NON_POSITIVE", name)
    return q
