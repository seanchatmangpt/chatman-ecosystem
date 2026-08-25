from fractions import Fraction
from .errors import Refused
from .sensitivity import Interval
def manski_mean(observed,missing,lower=Fraction(0),upper=Fraction(1)):
    observed=tuple(observed)
    if missing < 0 or lower > upper or any(not (lower <= x <= upper) for x in observed): raise Refused('REFUSED_MANSKI_DOMAIN')
    n=len(observed)+missing
    if n==0: raise Refused('REFUSED_EMPTY_IDENTIFICATION_SET')
    s=sum(observed,Fraction()); return Interval((s+missing*lower)/n,(s+missing*upper)/n)
