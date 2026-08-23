from fractions import Fraction
from math import log2
from .refusals import Refused

def unit(value, name="probability") -> Fraction:
    v = value if isinstance(value, Fraction) else Fraction(value)
    if v < 0 or v > 1:
        raise Refused(f"REFUSED_INVALID_{name.upper()}")
    return v

def normalized(values: dict[str, Fraction]) -> dict[str, Fraction]:
    if not values or any(not k for k in values):
        raise Refused("REFUSED_INVALID_DISTRIBUTION")
    vals = {k: unit(v) for k, v in values.items()}
    if sum(vals.values(), Fraction()) != 1:
        raise Refused("REFUSED_NON_NORMALIZED_DISTRIBUTION")
    return vals

def shannon_bits(values: dict[str, Fraction]) -> float:
    vals = normalized(values)
    return -sum(float(v) * log2(float(v)) for v in vals.values() if v)
