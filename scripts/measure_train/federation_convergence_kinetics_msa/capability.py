import math
from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class Capability:
    support: int
    successes: int
    probability: Fraction
    wilson_lower: float
    target: Fraction
    state: str

def on_time_capability(passages, deadline, target=Fraction(9, 10), z=1.96, min_support=10):
    rows = tuple(passages)
    if not rows:
        raise Refused("EMPTY_CAPABILITY_SAMPLE")
    successes = sum(1 for row in rows if row.event and row.duration <= deadline)
    n = len(rows)
    phat = successes / n
    z2 = z * z
    center = (phat + z2 / (2 * n)) / (1 + z2 / n)
    margin = z * math.sqrt(phat * (1 - phat) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    lower = max(0.0, center - margin)
    state = "INSUFFICIENT" if n < min_support else ("CAPABLE" if lower >= float(target) else "INCAPABLE")
    return Capability(n, successes, Fraction(successes, n), lower, target, state)
