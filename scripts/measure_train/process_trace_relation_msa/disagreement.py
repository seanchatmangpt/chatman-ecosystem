import math
from fractions import Fraction

def disagreement_rate(left:dict,right:dict):
    keys=set(left)|set(right)
    if not keys:
        return Fraction(0)
    return Fraction(sum(left.get(k)!=right.get(k) for k in keys),len(keys))

def binary_entropy(rate):
    p=float(rate)
    if p<=0 or p>=1:
        return 0.0
    return -(p*math.log2(p)+(1-p)*math.log2(1-p))
