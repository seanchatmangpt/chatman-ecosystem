from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class EffectiveSample:
    nominal:int; generalized:float; mean_pair_correlation:float
def effective_sample(m):
    n=len(m)
    if not n: raise Refused("REFUSED[EMPTY_FEDERATION]")
    total=sum(map(sum,m))
    if total<=0: raise Refused("REFUSED[INVALID_CORRELATION_MASS]")
    off=[m[i][j] for i in range(n) for j in range(i+1,n)]
    return EffectiveSample(n,min(float(n),n*n/total),sum(off)/len(off) if off else 0.0)
