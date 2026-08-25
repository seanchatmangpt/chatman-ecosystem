from .policy import Decision
from .errors import Refused
from .loss import realized_loss
def acted_coverage(observations): return sum(o.decision is not Decision.DEFER for o in observations)/len(observations)
def defer_rate(observations): return 1-acted_coverage(observations)
def selective_risk(policy, observations):
    acted=[o for o in observations if o.decision is not Decision.DEFER]
    if not acted: raise Refused("NO_ACTED_OBSERVATIONS")
    return sum((realized_loss(policy,o) for o in acted), realized_loss(policy,acted[0])*0)/len(acted)
