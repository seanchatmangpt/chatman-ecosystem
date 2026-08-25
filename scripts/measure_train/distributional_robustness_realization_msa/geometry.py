from fractions import Fraction
import math
from .refusal import Refused
def tv(a,b):
    keys=a.support|b.support
    return sum((abs(a.probability(k)-b.probability(k)) for k in keys),Fraction(0))/2
def hellinger(a,b):
    keys=a.support|b.support
    s=sum((math.sqrt(float(a.probability(k)))-math.sqrt(float(b.probability(k))))**2 for k in keys)
    return math.sqrt(s)/math.sqrt(2)
def chi_square(target,center):
    total=Fraction(0)
    for k in target.support|center.support:
        q=center.probability(k); p=target.probability(k)
        if q==0 and p>0: raise Refused("REFUSED[CHI_SQUARE_POSITIVITY]")
        if q>0: total+=(p-q)*(p-q)/q
    return total
def w1_two_support(a,b,distance):
    if distance<0: raise Refused("REFUSED[NEGATIVE_GROUND_COST]")
    keys=sorted(a.support|b.support)
    if len(keys)!=2: raise Refused("REFUSED[UNSUPPORTED_W1_SUPPORT]")
    return abs(a.probability(keys[0])-b.probability(keys[0]))*Fraction(distance)
