from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class Realization:
    selector: str; generation: int; chosen: tuple[str,...]; observed: tuple[str,...]; predicted_utility: Fraction; realized_utility: Fraction; cost: Fraction
    def __post_init__(self):
        if self.generation<0 or not self.selector or not self.chosen: raise Refused("INVALID_SELECTOR_REALIZATION")
        if any(x not in self.observed for x in self.chosen): raise Refused("UNOBSERVED_CHOSEN_EVIDENCE")
        if self.cost<0: raise Refused("INVALID_REALIZATION_COST")

def observed_regret(realized: Realization, observed_utilities: dict[str,Fraction]):
    missing=set(observed_utilities)-set(realized.observed)
    if missing: raise Refused("UNOBSERVED_COUNTERFACTUAL", ','.join(sorted(missing)))
    if not observed_utilities: raise Refused("NO_OBSERVED_ALTERNATIVES")
    best=max(observed_utilities.values())
    return max(Fraction(0), best-realized.realized_utility)
