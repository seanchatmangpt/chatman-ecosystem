from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True)
class TrialUtility:
    candidate_id: str
    realized_gain: float
    actual_cost: float

    @property
    def utility(self):
        return self.realized_gain/max(self.actual_cost,1e-12)


def ex_post_regret(chosen_id, observed_alternatives):
    rows=tuple(observed_alternatives)
    if not rows:
        raise Refused("REFUSED[NO_COUNTERFACTUAL_OBSERVATIONS]")
    chosen=[r for r in rows if r.candidate_id==chosen_id]
    if len(chosen)!=1:
        raise Refused("REFUSED[CHOSEN_COUNTERFACTUAL_IDENTITY]")
    best=max(r.utility for r in rows)
    return max(0.0,best-chosen[0].utility)
