from dataclasses import dataclass
from math import sqrt
from .errors import Refused
@dataclass(frozen=True)
class Wilson: n:int; successes:int; lower:float; upper:float
def wilson(successes,n,z=1.96):
    if n<=0 or not (0<=successes<=n): raise Refused("INVALID_AVAILABILITY_SAMPLE")
    p=successes/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; r=z*sqrt((p*(1-p)+z*z/(4*n))/n)/d
    return Wilson(n,successes,max(0,c-r),min(1,c+r))
