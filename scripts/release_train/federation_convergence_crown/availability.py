from math import sqrt
from .refusal import refuse
def wilson_lower(successes,total,z=1.96):
    if total<=0 or successes<0 or successes>total: refuse("INVALID_SUPPORT")
    p=successes/total; z2=z*z
    return (p+z2/(2*total)-z*sqrt((p*(1-p)+z2/(4*total))/total))/(1+z2/total)
