from fractions import Fraction
from .errors import Refused

def importance_weights(source, target, cap=Fraction(10)):
    s,t=source.as_dict(),target.as_dict(); out={}
    for k,tv in t.items():
        sv=s.get(k,0)
        if tv>0 and sv==0: raise Refused("POSITIVITY_VIOLATION", k)
        out[k]=min(tv/sv,cap) if sv else Fraction(0)
    return out

def effective_sample_size(weights):
    ws=[Fraction(w) for w in weights if w>0]
    if not ws: raise Refused("ZERO_WEIGHT_SUPPORT")
    return sum(ws)**2/sum(w*w for w in ws)
