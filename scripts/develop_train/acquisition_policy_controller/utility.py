from dataclasses import dataclass
from math import log1p
from .subject import Refusal
from .realization import Realization
@dataclass(frozen=True, slots=True)
class Utility:
    information:float
    cost_efficiency:float
    latency_efficiency:float
    risk_penalty:float
    score:float
def utility(r:Realization,*,failure_penalty:float=1.0):
    if failure_penalty<0: raise Refusal("REFUSED_INVALID_FAILURE_PENALTY")
    info=r.realized_gain; ce=info/(1+r.actual_cost); le=info/(1+r.actual_latency_ms); p=failure_penalty if r.outcome=="FAIL" else 0.0
    return Utility(info,ce,le,p,info+log1p(ce)+log1p(le)-p)
