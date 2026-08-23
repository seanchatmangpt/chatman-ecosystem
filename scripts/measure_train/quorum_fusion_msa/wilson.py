import math
def wilson_upper(errors:int, total:int, z:float=1.96):
    if total <= 0: return 1.0
    p=errors/total
    den=1+z*z/total
    center=(p+z*z/(2*total))/den
    margin=z*math.sqrt((p*(1-p)+z*z/(4*total))/total)/den
    return min(1.0, center+margin)
