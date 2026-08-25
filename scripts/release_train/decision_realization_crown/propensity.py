from .policy import Decision
from .errors import Refused
from .loss import realized_loss
def horvitz_thompson(policy, observations):
    acted=[o for o in observations if o.decision is not Decision.DEFER]
    if not acted: raise Refused("NO_ACTED_OBSERVATIONS")
    return sum(realized_loss(policy,o)/o.propensity for o in acted)/len(observations)
def self_normalized(policy, observations):
    acted=[o for o in observations if o.decision is not Decision.DEFER]
    if not acted: raise Refused("NO_ACTED_OBSERVATIONS")
    weights=[1/o.propensity for o in acted]
    return sum(w*realized_loss(policy,o) for w,o in zip(weights,acted))/sum(weights)
