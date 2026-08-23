from fractions import Fraction
from .errors import Refused

def observed_regret(chosen_loss: Fraction, observed_alternative_loss: Fraction | None):
    if observed_alternative_loss is None:
        raise Refused("UNOBSERVED_COUNTERFACTUAL")
    return max(Fraction(), chosen_loss-observed_alternative_loss)
