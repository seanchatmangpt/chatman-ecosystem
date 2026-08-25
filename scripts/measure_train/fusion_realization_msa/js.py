import math
from .probability import normalize
def _kl_bits(p,q):
    return sum(a*math.log2(a/b) for a,b in zip(p,q) if a>0)
def js_divergence(a,b):
    p,q=normalize(a),normalize(b)
    if len(p)!=len(q): raise ValueError("unaligned")
    m=tuple((x+y)/2 for x,y in zip(p,q))
    return 0.5*_kl_bits(p,m)+0.5*_kl_bits(q,m)
