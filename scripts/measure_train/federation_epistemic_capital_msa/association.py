import math
from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class PairAssociation:
    left:str; right:str; support:int; phi:float; mutual_information_bits:float
def associations(rows):
    by={}
    for r in rows: by.setdefault(r.transport.transport_id,{})[r.trial_id]=r
    if len(by)<2: raise Refused("REFUSED[INSUFFICIENT_TRANSPORTS]")
    common=set.intersection(*(set(v) for v in by.values()))
    if len(common)<2: raise Refused("REFUSED[INSUFFICIENT_ALIGNED_SUPPORT]")
    out=[]; ids=sorted(by); n=len(common)
    for i,x in enumerate(ids):
      for y in ids[i+1:]:
        ps=[(by[x][t].failed,by[y][t].failed) for t in common]
        a=sum(p and q for p,q in ps); b=sum(p and not q for p,q in ps); c=sum((not p) and q for p,q in ps); d=n-a-b-c
        den=(a+b)*(c+d)*(a+c)*(b+d); phi=0.0 if den==0 else (a*d-b*c)/math.sqrt(den)
        px={1:(a+b)/n,0:(c+d)/n}; py={1:(a+c)/n,0:(b+d)/n}; mi=0.0
        for (p,q),cnt in {(1,1):a,(1,0):b,(0,1):c,(0,0):d}.items():
          if cnt:
            z=cnt/n; mi+=z*math.log2(z/(px[p]*py[q]))
        out.append(PairAssociation(x,y,n,phi,mi))
    return tuple(out)
