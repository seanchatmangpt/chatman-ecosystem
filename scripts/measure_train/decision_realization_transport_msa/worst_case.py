from fractions import Fraction
def worst_stratum_risk(observations):
    by={}
    for o in observations: by.setdefault(o.stratum,[]).append(o.realized_loss)
    means={k:sum(v,Fraction(0))/len(v) for k,v in by.items()}
    return max(means.items(),key=lambda kv:kv[1]) if means else (None,Fraction(0))
