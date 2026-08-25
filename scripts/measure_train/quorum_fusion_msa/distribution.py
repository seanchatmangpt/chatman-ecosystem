import math
def normalized_error_vector(cal):
    raw=[cal.false_current_rate,cal.false_stale_rate,cal.ambiguity_rate,max(0.0,1-cal.false_current_rate-cal.false_stale_rate-cal.ambiguity_rate)]
    s=sum(raw)
    if s==0: return (0.0,0.0,0.0,1.0)
    return tuple(v/s for v in raw)
def kl(p,q):
    out=0.0
    for a,b in zip(p,q):
        if a>0: out+=a*math.log2(a/max(b,1e-15))
    return out
def jensen_shannon(p,q):
    m=tuple((a+b)/2 for a,b in zip(p,q))
    return 0.5*kl(p,m)+0.5*kl(q,m)
