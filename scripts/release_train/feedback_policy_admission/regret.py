from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class ObservedAlternative:
    strategy: str
    realized_gain: Fraction
def realized_regret(chosen_gain, alternatives):
    alts=tuple(alternatives)
    if not alts: raise Refused("UNOBSERVED_COUNTERFACTUAL")
    best=max((Fraction(a.realized_gain) for a in alts), default=None)
    if best is None: raise Refused("UNOBSERVED_COUNTERFACTUAL")
    return max(Fraction(0), best-Fraction(chosen_gain))
