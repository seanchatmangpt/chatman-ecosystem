from dataclasses import dataclass
from .population import Population
from .refusal import require

@dataclass(frozen=True)
class WeightWitness:
    weights: tuple[tuple[str,float], ...]
    ess: float
    maximum: float
    capped: bool


def importance_weights(source: Population, target: Population, cap: float | None = None) -> WeightWitness:
    require(cap is None or cap > 0, "INVALID_WEIGHT_CAP")
    s={k:float(v) for k,v in source.mass}; t={k:float(v) for k,v in target.mass}
    pairs=[]
    for k,tv in t.items():
        if tv <= 0: continue
        require(s.get(k,0.0)>0, "POSITIVITY_VIOLATION", k)
        w=tv/s[k]
        if cap is not None: w=min(w,cap)
        pairs.append((k,w))
    vals=[w for _,w in pairs]
    denom=sum(w*w for w in vals)
    ess=(sum(vals)**2/denom) if denom else 0.0
    return WeightWitness(tuple(sorted(pairs)),ess,max(vals,default=0.0),cap is not None)
