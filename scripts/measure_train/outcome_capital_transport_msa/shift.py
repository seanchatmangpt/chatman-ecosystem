import math
def total_variation(p,q):
    a,b=p.as_dict(),q.as_dict(); keys=set(a)|set(b)
    return 0.5*sum(abs(float(a.get(k,0)-b.get(k,0))) for k in keys)
def _kl(a,b):
    out=0.0
    for k,v in a.items():
        x=float(v); y=float(b.get(k,0))
        if x>0:
            if y<=0: return float("inf")
            out += x*math.log2(x/y)
    return out
def js_divergence(p,q):
    a,b=p.as_dict(),q.as_dict(); keys=set(a)|set(b)
    m={k:(a.get(k,0)+b.get(k,0))/2 for k in keys}
    return 0.5*_kl(a,m)+0.5*_kl(b,m)
