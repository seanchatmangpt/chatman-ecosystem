import math
from .subject import Refused

def phi_failure(left, right):
    if len(left) != len(right) or not left:
        raise Refused("REFUSED[INVALID_PAIR_SUPPORT]")
    a = b = c = d = 0
    for x, y in zip(left, right):
        if x and y: a += 1
        elif x and not y: b += 1
        elif not x and y: c += 1
        else: d += 1
    den = math.sqrt((a+b)*(c+d)*(a+c)*(b+d))
    return 0.0 if den == 0 else (a*d-b*c)/den
