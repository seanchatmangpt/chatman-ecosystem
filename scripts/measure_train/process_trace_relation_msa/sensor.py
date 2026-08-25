from collections import Counter
from .subject import Refused

def relation_sensor(cases):
    seen=set(); rows=[]
    for c in cases:
        key=(c.case_id,c.relation)
        if key in seen:
            raise Refused("REFUSED[DUPLICATE_LABELED_CASE]")
        seen.add(key); rows.append(c)
    return tuple(sorted(rows))

def perturbation_census(cases):
    return tuple(sorted(Counter(c.perturbation for c in cases).items()))
