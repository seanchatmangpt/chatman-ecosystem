from collections import Counter
from fractions import Fraction
def distribution(observations):
    rows=tuple(observations)
    if not rows:return {}
    c=Counter(o.stratum for o in rows); n=len(rows)
    return {k:Fraction(v,n) for k,v in sorted(c.items(),key=lambda kv:kv[0])}
