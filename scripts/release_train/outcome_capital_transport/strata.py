from collections import defaultdict
from fractions import Fraction
from .errors import Refused

def by_stratum(observations, losses):
    groups=defaultdict(list)
    for o,l in zip(observations,losses):
        groups[(o.methodology,o.engine,o.region,o.evidence_root)].append(Fraction(l))
    return {k:sum(v,Fraction(0))/len(v) for k,v in sorted(groups.items())}

def worst_stratum(observations, losses, ceiling=Fraction(2)):
    groups=by_stratum(observations,losses)
    if not groups: raise Refused("EMPTY_STRATA")
    worst=max(groups.items(), key=lambda kv: kv[1])
    if worst[1]>ceiling: raise Refused("STRATUM_RISK_EXCEEDED", repr(worst[0]))
    return worst
