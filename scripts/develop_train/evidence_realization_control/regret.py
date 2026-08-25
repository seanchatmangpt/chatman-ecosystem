from .errors import Refused
def observed_regret(chosen_utility, observed_alternatives):
    observed_alternatives=tuple(observed_alternatives)
    if not observed_alternatives: raise Refused('REFUSED[UNOBSERVED_COUNTERFACTUAL]')
    return max(0.0,max(observed_alternatives)-chosen_utility)
