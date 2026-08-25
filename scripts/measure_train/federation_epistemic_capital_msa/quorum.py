from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class QuorumRealization:
    nominal:int; effective_n:float; required:float; predicted:bool; realized:bool; admitted:bool; error:str
def realize(rows,capital,required):
    if required<=0: raise Refused("REFUSED[INVALID_EFFECTIVE_QUORUM]")
    latest={}
    for r in rows: latest[r.transport.transport_id]=r
    pred=sum(r.predicted_current for r in latest.values())>=2; real=sum(r.realized_current for r in latest.values())>=2
    ok=pred and real and capital.effective_n>=required
    err="FALSE_CURRENT" if pred and not real else "FALSE_STALE" if real and not pred else "PSEUDO_QUORUM" if pred and real and not ok else "NONE"
    return QuorumRealization(len(latest),capital.effective_n,float(required),pred,real,ok,err)
