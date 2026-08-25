from .policy import Decision
def realized_loss(policy, obs):
    if obs.decision is Decision.DEFER: return policy.loss.defer
    predicted_independent = obs.decision is Decision.INDEPENDENT
    if predicted_independent == obs.truth_independent: return policy.loss.defer * 0
    return policy.loss.false_independent if predicted_independent else policy.loss.false_dependent
def mean_loss(policy, observations):
    vals=[realized_loss(policy,o) for o in observations]
    return sum(vals, vals[0]*0)/len(vals)
