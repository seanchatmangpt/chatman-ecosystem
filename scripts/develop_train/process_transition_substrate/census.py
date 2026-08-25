from collections import Counter
from fractions import Fraction
from .obligation import State
from .errors import Refused
def census(obligations):
    items=list(obligations)
    keys=[o.key for o in items]
    if len(keys)!=len(set(keys)): raise Refused("REFUSED[DUPLICATE_OBLIGATION]")
    counts=Counter(o.state for o in items)
    closed=sum(counts[s] for s in (State.PASS,State.UNSUPPORTED))
    return {"total":len(items),"counts":dict(counts),"closure":Fraction(closed,len(items)) if items else Fraction(0,1)}
