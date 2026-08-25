from collections import defaultdict
from fractions import Fraction
def by_stratum(cases):
    groups=defaultdict(list)
    for c in cases: groups[(c.methodology,c.engine,c.region,c.evidence_root)].append(c)
    return {k:tuple(v) for k,v in sorted(groups.items())}
def worst_stratum_risk(cases):
    groups=by_stratum(cases)
    if not groups:return None
    scored=[]
    for key,rows in groups.items():
        risk=sum((r.observed_risk for r in rows),Fraction(0))/len(rows); scored.append((risk,key,len(rows)))
    return max(scored)
