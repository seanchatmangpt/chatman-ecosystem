from dataclasses import dataclass
from fractions import Fraction
from .belief import entropy_reduction
from .subject import Refused

@dataclass(frozen=True)
class RealizedInformation:
    predicted_gain: Fraction
    realized_gain: float
    gain_error: float
    sign: str


def realize(plan, outcome, prior_defect: Fraction) -> RealizedInformation:
    if plan.subject != outcome.subject or plan.plan_id != outcome.plan_id or plan.candidate_id != outcome.candidate_id:
        raise Refused("REFUSED[PLAN_OUTCOME_IDENTITY_MISMATCH]")
    gain=entropy_reduction(prior_defect,outcome.posterior_defect)
    error=gain-float(plan.predicted_gain)
    sign="POSITIVE" if gain>0 else "ZERO" if abs(gain)<1e-15 else "NEGATIVE"
    return RealizedInformation(plan.predicted_gain,gain,error,sign)
