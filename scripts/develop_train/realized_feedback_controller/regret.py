from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class ObservedAlternative:
    policy_id: str
    realized_gain: Fraction
    cost: Fraction

def realized_regret(selected: ObservedAlternative, alternatives: tuple[ObservedAlternative, ...]):
    if not alternatives:
        raise Refused("REFUSED_UNOBSERVED_COUNTERFACTUAL")
    utility=lambda x: x.realized_gain-x.cost
    best=max(utility(a) for a in alternatives+(selected,))
    return max(Fraction(), best-utility(selected))
