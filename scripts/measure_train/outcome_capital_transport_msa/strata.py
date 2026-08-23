from .subject import Refused
from .loss import realized_loss
from fractions import Fraction
def key(o): return (o.methodology,o.engine,o.region,o.evidence_root)
def group(observations):
    out={}
    for o in observations: out.setdefault(key(o),[]).append(o)
    return {k:tuple(v) for k,v in sorted(out.items())}
def worst_stratum(observations,matrix,min_support=1):
    g=group(observations); scored=[]
    for k,rows in g.items():
        labeled=[o for o in rows if o.labeled]
        if len(labeled)<min_support: raise Refused("REFUSED[INSUFFICIENT_STRATUM_SUPPORT]")
        risk=sum((realized_loss(o,matrix) for o in labeled),Fraction(0))/len(labeled)
        scored.append((risk,k))
    return max(scored) if scored else (Fraction(0),None)
