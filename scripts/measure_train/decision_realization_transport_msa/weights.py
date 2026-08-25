from fractions import Fraction
from .errors import Refused
def importance_weights(source_dist,target_dist,max_weight=Fraction(10)):
    out={}
    for k,t in target_dist.items():
        s=source_dist.get(k,Fraction(0))
        if t>0 and s==0: raise Refused("REFUSED[POSITIVITY_VIOLATION]")
        w=t/s if s else Fraction(0)
        out[k]=min(w,max_weight)
    return out
def effective_sample_size(observations,weights):
    ws=[weights[o.stratum] for o in observations if o.stratum in weights]
    if not ws:return Fraction(0)
    return sum(ws)**2/sum(w*w for w in ws)
