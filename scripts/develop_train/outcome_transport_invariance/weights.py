from dataclasses import dataclass
from .support import require
from .errors import Refused

@dataclass(frozen=True)
class Weights:
    items: tuple
    ess: float
    maximum: float
    capped: bool

def make(source, target, cap=None):
    require(source, target)
    s, t = source.data(), target.data()
    out, capped = [], False
    for cell, mass in sorted(t.items()):
        if mass <= 0:
            continue
        weight = mass / s[cell]
        if cap is not None:
            if cap <= 0:
                raise Refused("INVALID_CAP")
            capped |= weight > cap
            weight = min(weight, cap)
        out.append((cell, weight))
    values = [w for _, w in out]
    square_sum = sum(w * w for w in values)
    ess = sum(values) ** 2 / square_sum if square_sum else 0
    return Weights(tuple(out), ess, max(values) if values else 0, capped)

def require_ess(weights, minimum):
    if weights.ess < minimum:
        raise Refused("ESS_COLLAPSE")
    return weights
