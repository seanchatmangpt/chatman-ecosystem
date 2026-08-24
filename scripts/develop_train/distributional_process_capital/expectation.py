from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

def expectation(distribution,loss):
    missing=distribution.support-set(loss)
    if missing:
        raise Refused("LOSS_MISSING",",".join(sorted(missing)))
    return sum((distribution.get(k)*Fraction(loss[k]) for k in distribution.support),Fraction(0))
@dataclass(frozen=True)
class WorstCase:
    value: Fraction
    witness: object

def worst_case(ambiguity,candidates,loss):
    admitted=[d for d in candidates if ambiguity.contains(d)]
    if not admitted:
        raise Refused("NO_ADMITTED_AMBIGUITY_WITNESS")
    scored=[(expectation(d,loss),d) for d in admitted]
    value,witness=max(scored,key=lambda item:(item[0],item[1].mass))
    return WorstCase(value,witness)
