from fractions import Fraction
from .errors import Refused

def unit(value) -> Fraction:
    try:
        result = value if isinstance(value, Fraction) else Fraction(value)
    except (ValueError, TypeError, ZeroDivisionError):
        raise Refused("INVALID_RATIONAL") from None
    if result < 0 or result > 1:
        raise Refused("RATIONAL_OUT_OF_UNIT_INTERVAL")
    return result

def positive(value) -> Fraction:
    try:
        result = value if isinstance(value, Fraction) else Fraction(value)
    except (ValueError, TypeError, ZeroDivisionError):
        raise Refused("INVALID_RATIONAL") from None
    if result <= 0:
        raise Refused("NON_POSITIVE_VALUE")
    return result
