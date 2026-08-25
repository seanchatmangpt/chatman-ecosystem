from .loss import realized_loss
from .errors import Refused

def horvitz_thompson(policy, observations):
    labeled = [o for o in observations if o.truth_independent is not None]
    if not labeled:
        raise Refused("NO_LABELED_OUTCOMES")
    return sum(realized_loss(policy, o) / o.propensity for o in labeled) / len(observations)

def self_normalized(policy, observations):
    labeled = [o for o in observations if o.truth_independent is not None]
    if not labeled:
        raise Refused("NO_LABELED_OUTCOMES")
    weights = [1.0/o.propensity for o in labeled]
    denom = sum(weights)
    if denom == 0:
        raise Refused("ZERO_PROPENSITY_MASS")
    return sum(w * realized_loss(policy, o) for w, o in zip(weights, labeled)) / denom

def selective_risk(policy, observations):
    acted = [o for o in observations if o.decision.value != "DEFER" and o.truth_independent is not None]
    if not acted:
        raise Refused("NO_ACTED_LABELED_OUTCOMES")
    return sum(realized_loss(policy, o) for o in acted) / len(acted)
