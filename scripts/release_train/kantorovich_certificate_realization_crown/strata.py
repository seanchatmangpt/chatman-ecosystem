from collections import defaultdict
def group(observations, field):
    d=defaultdict(list)
    for o in observations: d[getattr(o,field)].append(o)
    return dict(d)
def worst_stratum(observations, field):
    from .consequence import evaluate
    scored=[(evaluate(v).mae,k) for k,v in group(observations,field).items()]
    return max(scored)[1]
