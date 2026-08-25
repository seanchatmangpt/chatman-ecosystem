from .errors import Refused
from .loss import realized_loss
def observed_regret(policy, obs, alternative_loss=None):
    if alternative_loss is None: raise Refused("UNOBSERVED_COUNTERFACTUAL")
    loss=realized_loss(policy,obs)
    return max(loss-loss.__class__(alternative_loss), loss*0)
