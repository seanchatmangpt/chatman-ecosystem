import math
from dataclasses import dataclass

def _term(p, px, py):
    if p <= 0 or px <= 0 or py <= 0:
        return 0.0
    return p*math.log2(p/(px*py))

@dataclass(frozen=True)
class InformationProfile:
    mutual_information_bits: float
    entropy_left_bits: float
    entropy_right_bits: float
    normalized_mi: float

def profile(table):
    n=table.n
    if not n:
        return InformationProfile(0.0,0.0,0.0,0.0)
    probs={(0,0):table.n00/n,(0,1):table.n01/n,(1,0):table.n10/n,(1,1):table.n11/n}
    px={0:(table.n00+table.n01)/n,1:(table.n10+table.n11)/n}
    py={0:(table.n00+table.n10)/n,1:(table.n01+table.n11)/n}
    mi=sum(_term(p,px[x],py[y]) for (x,y),p in probs.items())
    def h(v):
        return -sum(p*math.log2(p) for p in v.values() if p>0)
    hx,hy=h(px),h(py)
    denom=min(hx,hy)
    return InformationProfile(mi,hx,hy,0.0 if denom==0 else mi/denom)
