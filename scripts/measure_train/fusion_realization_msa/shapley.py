import math
from itertools import combinations
from .subject import Refused
def shapley_values(sensor_ids, value_fn, max_sensors=8):
    ids=tuple(sensor_ids); n=len(ids)
    if not ids or n>max_sensors or len(set(ids))!=n: raise Refused("REFUSED[UNBOUNDED_SHAPLEY_SET]")
    result={s:0.0 for s in ids}
    for s in ids:
        others=[x for x in ids if x!=s]
        for k in range(len(others)+1):
            weight=math.factorial(k)*math.factorial(n-k-1)/math.factorial(n)
            for subset in combinations(others,k):
                base=frozenset(subset); result[s]+=weight*(value_fn(base|{s})-value_fn(base))
    return tuple(sorted(result.items()))
