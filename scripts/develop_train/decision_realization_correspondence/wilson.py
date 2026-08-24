import math
from fractions import Fraction

def wilson_upper(errors: int, n: int, z: float=1.96) -> Fraction:
    if n <= 0 or errors < 0 or errors > n:
        raise ValueError("invalid counts")
    p=errors/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    radius=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return Fraction.from_float(min(1.0,center+radius)).limit_denominator(10**6)
