from fractions import Fraction
from .errors import Refused

def overlap(source, target):
    s, t = source.as_dict(), target.as_dict()
    supported=sum((v for k,v in t.items() if s.get(k,0)>0), Fraction(0))
    missing=tuple(sorted(k for k,v in t.items() if v>0 and s.get(k,0)==0))
    return supported, missing

def require_positivity(source, target):
    supported, missing = overlap(source,target)
    if missing: raise Refused("POSITIVITY_VIOLATION", ",".join(missing))
    return supported
