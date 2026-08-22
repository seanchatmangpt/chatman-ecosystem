from dataclasses import dataclass
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class DriftState:
    mean:float=0.0
    cumulative:float=0.0
    minimum:float=0.0
    n:int=0
    drifted:bool=False
def page_hinkley(s:DriftState,x:float,*,delta:float=0.01,threshold:float=0.25):
    if delta<0 or threshold<=0: raise Refusal("REFUSED_INVALID_DRIFT_PARAMETERS")
    n=s.n+1; mean=s.mean+(x-s.mean)/n; c=s.cumulative+(x-mean-delta); m=min(s.minimum,c)
    return DriftState(mean,c,m,n,(c-m)>threshold)
