from math import sqrt
from .refusal import Refused

def wilson_lower(successes: int, total: int, z: float=1.96) -> float:
    if total <= 0 or not 0 <= successes <= total:
        raise Refused("INVALID_WILSON_SUPPORT")
    p=successes/total
    denom=1+z*z/total
    center=p+z*z/(2*total)
    margin=z*sqrt((p*(1-p)+z*z/(4*total))/total)
    return max(0.0, (center-margin)/denom)
