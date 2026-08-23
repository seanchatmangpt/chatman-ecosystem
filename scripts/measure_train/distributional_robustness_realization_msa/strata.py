from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True, order=True)
class Stratum:
    methodology:str; engine:str; region:str; evidence_root:str
def worst_stratum(observations):
    buckets={}
    for r in observations:
        key=Stratum(r.methodology,r.engine,r.region,r.evidence_root); buckets.setdefault(key,[]).append(r)
    scored=[]
    for key,rows in buckets.items():
        miss=sum(1 for r in rows if r.realized_loss>r.predicted_worst_loss); scored.append((Fraction(miss,len(rows)),key,len(rows)))
    return max(scored,default=(Fraction(0),None,0),key=lambda x:(x[0],-x[2],x[1] or Stratum('','','','')))
