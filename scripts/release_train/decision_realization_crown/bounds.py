import math
from .errors import Refused
def wilson_upper(errors:int,n:int,z:float=1.96):
    if n<=0 or errors<0 or errors>n: raise Refused("INVALID_WILSON_SAMPLE")
    p=errors/n; z2=z*z; den=1+z2/n
    center=(p+z2/(2*n))/den; radius=z*math.sqrt((p*(1-p)+z2/(4*n))/n)/den
    return min(1.0,center+radius)
