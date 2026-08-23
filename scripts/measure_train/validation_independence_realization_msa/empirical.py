import math
from dataclasses import dataclass
@dataclass(frozen=True)
class PairStats:
    support:int; overlap_rate:float; phi:float; mutual_information:float
def measure_pairs(rows):
    rows=tuple(rows); n=len(rows)
    if not n:return PairStats(0,0.0,0.0,0.0)
    counts={(0,0):0,(0,1):0,(1,0):0,(1,1):0}
    for a,b in rows: counts[(int(bool(a)),int(bool(b)))]+=1
    p1=(counts[(1,0)]+counts[(1,1)])/n; p2=(counts[(0,1)]+counts[(1,1)])/n; p11=counts[(1,1)]/n
    den=math.sqrt(max(p1*(1-p1)*p2*(1-p2),0.0)); phi=(p11-p1*p2)/den if den else 0.0
    mi=0.0
    for (a,b),c in counts.items():
        if not c:continue
        pab=c/n; pa=sum(v for (x,_),v in counts.items() if x==a)/n; pb=sum(v for (_,y),v in counts.items() if y==b)/n
        mi += pab*math.log2(pab/(pa*pb))
    return PairStats(n,p11,phi,mi)
