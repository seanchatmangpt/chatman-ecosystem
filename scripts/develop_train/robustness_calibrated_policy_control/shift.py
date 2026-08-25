from fractions import Fraction
from .refusal import Refused
def total_variation(p:tuple[Fraction,...],q:tuple[Fraction,...])->Fraction:
    if len(p)!=len(q) or not p: raise Refused('SHIFT_DIMENSION')
    if sum(p)!=1 or sum(q)!=1 or any(x<0 for x in p+q): raise Refused('INVALID_DISTRIBUTION')
    return sum(abs(a-b) for a,b in zip(p,q))/2
def shift_adjust(interval, radius:Fraction, lipschitz:Fraction):
    from .interval import Interval
    if radius<0 or radius>1 or lipschitz<0: raise Refused('INVALID_SHIFT_BOUND')
    penalty=radius*lipschitz
    return Interval(interval.lower-penalty, interval.upper+penalty)
