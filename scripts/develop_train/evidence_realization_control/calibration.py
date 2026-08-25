import math
from dataclasses import dataclass
from .errors import Refused
def wilson_upper(k,n,z=1.96):
    if n<=0 or k<0 or k>n: raise Refused('REFUSED[INVALID_SAMPLE]')
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/d
    return min(1.0,c+h)
@dataclass(frozen=True)
class Calibration:
    support:int; error_upper:float; mean_regret:float
    @classmethod
    def from_observations(cls, errors, regrets):
        errors=tuple(errors); regrets=tuple(regrets); n=len(errors)
        if n<4 or len(regrets)!=n: raise Refused('REFUSED[INSUFFICIENT_REALIZATION_SUPPORT]')
        k=sum(1 for e in errors if e>0.5)
        return cls(n,wilson_upper(k,n),sum(regrets)/n)
