import math
from .subject import Refused
def normalize(values, tol=1e-12):
    xs=tuple(float(x) for x in values)
    if not xs or any((not math.isfinite(x) or x < 0) for x in xs): raise Refused("REFUSED[INVALID_DISTRIBUTION]")
    total=sum(xs)
    if total <= tol: raise Refused("REFUSED[ZERO_MASS_DISTRIBUTION]")
    return tuple(x/total for x in xs)
def aligned(distributions):
    rows=[normalize(d) for d in distributions]
    if not rows or len({len(r) for r in rows})!=1: raise Refused("REFUSED[UNALIGNED_DISTRIBUTIONS]")
    return tuple(rows)
