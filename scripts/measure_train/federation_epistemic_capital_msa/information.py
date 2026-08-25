import math
from dataclasses import dataclass
@dataclass(frozen=True)
class InformationCapital:
    raw_bits:float; redundancy_bits:float; effective_bits:float
def measure(rows,assoc,capital):
    latest={}
    for r in rows: latest[r.transport.transport_id]=r
    vals=[int(r.failed) for r in latest.values()]; p=sum(vals)/len(vals) if vals else 0.0
    raw=0.0 if p in (0.0,1.0) else -p*math.log2(p)-(1-p)*math.log2(1-p)
    red=sum(a.mutual_information_bits for a in assoc); eff=raw*capital.effective_n/max(1,capital.nominal)
    return InformationCapital(raw,red,max(0.0,eff))
