import math
from dataclasses import dataclass

@dataclass(frozen=True)
class TripleSynergy:
    total_correlation_bits:float
    pairwise_max_mi_bits:float
    higher_order_excess_bits:float

def _entropy(values):
    counts={}
    for v in values: counts[v]=counts.get(v,0)+1
    n=len(values)
    return -sum((c/n)*math.log2(c/n) for c in counts.values()) if n else 0.0

def triple_synergy(rows):
    rows=tuple(rows)
    if not rows: return TripleSynergy(0.0,0.0,0.0)
    xs=[r[0] for r in rows]; ys=[r[1] for r in rows]; zs=[r[2] for r in rows]
    hsum=_entropy(xs)+_entropy(ys)+_entropy(zs)
    hjoint=_entropy(list(zip(xs,ys,zs)))
    total=hsum-hjoint
    pairmis=[]
    for a,b in ((xs,ys),(xs,zs),(ys,zs)):
        pairmis.append(_entropy(a)+_entropy(b)-_entropy(list(zip(a,b))))
    pmax=max(pairmis)
    return TripleSynergy(total,pmax,max(0.0,total-pmax))
