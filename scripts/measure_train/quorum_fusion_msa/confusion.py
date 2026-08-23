from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class Confusion:
    tp:int; fp:int; tn:int; fn:int; ambiguous:int
    @property
    def support(self): return self.tp+self.fp+self.tn+self.fn+self.ambiguous
    @property
    def false_current_rate(self):
        d=self.fp+self.tn
        return self.fp/d if d else 0.0
    @property
    def false_stale_rate(self):
        d=self.fn+self.tp
        return self.fn/d if d else 0.0
def confusion(trials):
    seen=set(); tp=fp=tn=fn=amb=0
    for t in trials:
        k=(t.sensor.sensor_id,t.case_id)
        if k in seen: raise Refused("REFUSED[DUPLICATE_TRIAL]")
        seen.add(k)
        if t.prediction=="AMBIGUOUS": amb+=1
        elif t.truth=="CURRENT" and t.prediction=="CURRENT": tp+=1
        elif t.truth=="STALE" and t.prediction=="CURRENT": fp+=1
        elif t.truth=="STALE" and t.prediction=="STALE": tn+=1
        else: fn+=1
    return Confusion(tp,fp,tn,fn,amb)
