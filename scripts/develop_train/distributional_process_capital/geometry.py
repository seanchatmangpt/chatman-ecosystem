from fractions import Fraction
from math import sqrt
from .errors import Refused

def total_variation(p,q):
    keys=p.support|q.support
    return sum((abs(p.get(k)-q.get(k)) for k in keys), Fraction(0))/2

def overlap(p,q):
    keys=p.support|q.support
    return sum((min(p.get(k),q.get(k)) for k in keys), Fraction(0))

def hellinger(p,q):
    keys=p.support|q.support
    return sqrt(sum((sqrt(float(p.get(k)))-sqrt(float(q.get(k))))**2 for k in keys)/2)

def chi_square(candidate,center):
    if not candidate.support <= center.support:
        raise Refused("POSITIVITY_VIOLATION")
    total=Fraction(0)
    for k in center.support:
        c=center.get(k)
        if c<=0:
            raise Refused("ZERO_CENTER_SUPPORT",k)
        d=candidate.get(k)-c
        total += d*d/c
    return total
