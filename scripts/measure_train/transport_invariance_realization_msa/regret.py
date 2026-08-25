from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class ObservedAlternative:
    case_id:str
    strategy:str
    observed_risk:Fraction
def observed_regret(chosen,alternatives):
    rows=[a for a in alternatives if a.case_id==chosen.case_id]
    if not rows: raise Refused("REFUSED[UNOBSERVED_COUNTERFACTUAL]")
    return max(Fraction(0),chosen.observed_risk-min(a.observed_risk for a in rows))
