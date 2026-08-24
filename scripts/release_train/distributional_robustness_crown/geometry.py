from fractions import Fraction
from math import sqrt
from .refusal import Refused
def total_variation(a,b):
    keys=a.support|b.support; am=a.mapping(); bm=b.mapping()
    return sum((abs(am.get(k,Fraction())-bm.get(k,Fraction())) for k in keys), Fraction())/2
def hellinger(a,b):
    keys=a.support|b.support; am=a.mapping(); bm=b.mapping()
    return sqrt(sum((sqrt(float(am.get(k,0)))-sqrt(float(bm.get(k,0))))**2 for k in keys)/2)
def chi_square(candidate, reference):
    cm=candidate.mapping(); rm=reference.mapping(); out=Fraction()
    for k,p in cm.items():
        q=rm.get(k,Fraction())
        if p and not q: raise Refused("POSITIVITY_VIOLATION", k)
        if q: out += (p-q)**2/q
    return out
def wasserstein1(a,b,cost):
    if len(a.support|b.support) != 2: raise Refused("UNSUPPORTED_W1_DIMENSION")
    x,y=sorted(a.support|b.support); c=Fraction(str(cost.get((x,y),cost.get((y,x),0))))
    if c <= 0: raise Refused("MISSING_GROUND_COST")
    return abs(a.mapping().get(x,Fraction())-b.mapping().get(x,Fraction()))*c
