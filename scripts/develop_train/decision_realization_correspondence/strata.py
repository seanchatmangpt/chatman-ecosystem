from collections import defaultdict
from fractions import Fraction
from .realized_loss import realized_loss

def by_stratum(policy, observations):
    groups=defaultdict(list)
    for o in observations:
        key=(o.methodology,o.engine,o.region,o.evidence_root)
        groups[key].append(o)
    return {k: sum((realized_loss(policy,o) for o in xs), Fraction())/len(xs) for k,xs in groups.items()}
