from .policy import Decision
from .errors import Refused

def realized_loss(policy, observation):
    if observation.truth_independent is None:
        raise Refused("UNOBSERVED_OUTCOME")
    if observation.decision == Decision.DEFER:
        return policy.loss.defer + observation.realized_cost
    predicted_independent = observation.decision == Decision.INDEPENDENT
    if predicted_independent == observation.truth_independent:
        return observation.realized_cost
    if predicted_independent:
        return policy.loss.false_independent + observation.realized_cost
    return policy.loss.false_dependent + observation.realized_cost

def losses(policy, observations):
    return tuple(realized_loss(policy, o) for o in observations if o.truth_independent is not None)
