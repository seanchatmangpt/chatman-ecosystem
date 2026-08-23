from fractions import Fraction
from .intervals import Interval
from .refusal import Refused

def total_variation(p: tuple[Fraction, ...], q: tuple[Fraction, ...]) -> Fraction:
    if len(p) != len(q) or not p: raise Refused("INVALID_DISTRIBUTION_DIMENSION")
    if any(x < 0 for x in p + q) or sum(p) != 1 or sum(q) != 1:
        raise Refused("INVALID_DISTRIBUTION")
    return sum(abs(a-b) for a,b in zip(p,q)) / 2

def shift_adjust(interval: Interval, radius: Fraction, lipschitz: Fraction) -> Interval:
    if radius < 0 or radius > 1 or lipschitz < 0: raise Refused("INVALID_SHIFT_BOUND")
    return interval.expand(radius * lipschitz)
