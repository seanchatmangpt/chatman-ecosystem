from fractions import Fraction
from .realized_loss import realized_loss

def acted_coverage(observations):
    acted=sum(o.decision!="DEFER" for o in observations)
    return Fraction(acted, len(observations))

def defer_rate(observations):
    return 1-acted_coverage(observations)

def selective_risk(policy, observations):
    acted=[o for o in observations if o.decision!="DEFER"]
    if not acted:
        return None
    return sum((realized_loss(policy,o) for o in acted), Fraction())/len(acted)
