import math

def wilson_lower(successes:int,total:int,z:float=1.96)->float:
    if total <= 0:
        return 0.0
    p=successes/total
    z2=z*z
    centre=p+z2/(2*total)
    margin=z*math.sqrt((p*(1-p)+z2/(4*total))/total)
    return max(0.0,(centre-margin)/(1+z2/total))
