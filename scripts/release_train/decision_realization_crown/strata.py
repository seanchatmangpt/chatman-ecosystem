from collections import defaultdict
from .loss import mean_loss
from .errors import Refused
def by_stratum(policy,observations,attr):
    groups=defaultdict(list)
    for o in observations: groups[getattr(o,attr)].append(o)
    return {k:mean_loss(policy,v) for k,v in sorted(groups.items())}
def require_strata(policy,observations,max_loss):
    for attr in ("methodology","engine","region","evidence_root"):
        if any(v>max_loss for v in by_stratum(policy,observations,attr).values()): raise Refused(f"STRATUM_RISK_EXCEEDED:{attr}")
    return True
