from dataclasses import dataclass
from collections import Counter
from .normalize import activity
@dataclass(frozen=True)
class Conformance:
    precision:float; recall:float; f1:float
def score(reference,observed):
    r,o=Counter(activity(reference)),Counter(activity(observed)); hit=sum((r&o).values())
    p=hit/max(1,sum(o.values())); q=hit/max(1,sum(r.values())); f=0.0 if p+q==0 else 2*p*q/(p+q)
    return Conformance(p,q,f)
