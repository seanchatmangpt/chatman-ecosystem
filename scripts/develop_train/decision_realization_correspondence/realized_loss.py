from fractions import Fraction

def realized_loss(policy, o):
    if o.decision == "DEFER":
        return policy.losses.defer + o.realized_cost
    if o.truth is None:
        return o.realized_cost
    if o.decision == o.truth:
        return o.realized_cost
    if o.decision == "INDEPENDENT":
        return policy.losses.false_independent + o.realized_cost
    return policy.losses.false_dependent + o.realized_cost

def mean_loss(policy, observations):
    vals=[realized_loss(policy,o) for o in observations]
    return sum(vals, Fraction()) / len(vals)
