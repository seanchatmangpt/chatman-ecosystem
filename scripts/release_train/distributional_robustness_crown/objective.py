from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
def expectation(distribution, losses):
    missing=distribution.support-set(losses)
    if missing: raise Refused("MISSING_LOSS", sorted(missing)[0])
    return sum((p*Fraction(str(losses[k])) for k,p in distribution.mass),Fraction())
@dataclass(frozen=True)
class WorstCase:
    value: Fraction; witness: object
def worst_case(ambiguity,candidates,losses):
    admitted=[c for c in candidates if ambiguity.admits(c)]
    if not admitted: raise Refused("EMPTY_AMBIGUITY_WITNESS_SET")
    scored=[(expectation(c,losses),c) for c in admitted]
    value,witness=max(scored,key=lambda x:(x[0],x[1].mass))
    return WorstCase(value,witness)
