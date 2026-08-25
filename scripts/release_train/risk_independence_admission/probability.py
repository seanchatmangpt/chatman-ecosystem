from fractions import Fraction
from .errors import Refused

def q(value, code='INVALID_RATIONAL'):
    try: x=Fraction(value)
    except Exception as e: raise Refused(code) from e
    return x
def unit(value):
    x=q(value,'INVALID_PROBABILITY')
    if not 0 <= x <= 1: raise Refused('PROBABILITY_OUT_OF_RANGE')
    return x
def nonnegative(value):
    x=q(value,'INVALID_NONNEGATIVE')
    if x < 0: raise Refused('NEGATIVE_VALUE')
    return x
def positive(value):
    x=q(value,'INVALID_POSITIVE')
    if x <= 0: raise Refused('NONPOSITIVE_VALUE')
    return x
