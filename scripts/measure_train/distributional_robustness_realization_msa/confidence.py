import math
from dataclasses import dataclass
@dataclass(frozen=True)
class Wilson:
    lower:float; upper:float
def wilson(successes,n,z=1.959963984540054):
    if n<=0: return Wilson(0.0,1.0)
    p=successes/n; den=1+z*z/n; center=(p+z*z/(2*n))/den
    margin=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return Wilson(max(0.0,center-margin),min(1.0,center+margin))
