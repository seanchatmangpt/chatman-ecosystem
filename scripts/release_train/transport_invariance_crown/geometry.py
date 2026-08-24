from dataclasses import dataclass
from math import log, sqrt
from .population import Population

@dataclass(frozen=True)
class Geometry:
    total_variation: float
    hellinger: float
    jensen_shannon: float


def population_geometry(source: Population, target: Population) -> Geometry:
    s={k:float(v) for k,v in source.mass}; t={k:float(v) for k,v in target.mass}
    keys=set(s)|set(t)
    tv=0.5*sum(abs(s.get(k,0.0)-t.get(k,0.0)) for k in keys)
    h=sqrt(0.5*sum((sqrt(s.get(k,0.0))-sqrt(t.get(k,0.0)))**2 for k in keys))
    def kl(p, q):
        return sum(pv*log(pv/q[k],2) for k,pv in p.items() if pv>0 and q[k]>0)
    m={k:(s.get(k,0.0)+t.get(k,0.0))/2 for k in keys}
    js=0.5*kl({k:s.get(k,0.0) for k in keys},m)+0.5*kl({k:t.get(k,0.0) for k in keys},m)
    return Geometry(tv,h,js)
