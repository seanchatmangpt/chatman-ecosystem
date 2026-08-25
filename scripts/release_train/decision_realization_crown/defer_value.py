from .policy import Decision
from .errors import Refused
def realized_defer_value(obs, risk_before, risk_after):
    if obs.decision is not Decision.DEFER: raise Refused("NOT_A_DEFER_OBSERVATION")
    before=obs.predicted_risk.__class__(risk_before); after=obs.predicted_risk.__class__(risk_after)
    return before-after-obs.evidence_cost-obs.latency_cost
