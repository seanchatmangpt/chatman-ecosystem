from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class Calibration:
    generation:int; support:int; miss_rate:float; mean_width:float; digest:str; current:bool=True
    def __post_init__(self):
        if self.generation<0 or self.support<1 or not (0<=self.miss_rate<=1) or self.mean_width<0: raise Refused("INVALID_CALIBRATION")
def current(records):
    live=[r for r in records if r.current]
    if not live: raise Refused("NO_CURRENT_CALIBRATION")
    g=max(r.generation for r in live); xs=[r for r in live if r.generation==g]
    if len({(x.digest,x.support,x.miss_rate,x.mean_width) for x in xs})!=1: raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    return xs[0]
class Cusum:
    def __init__(self,threshold,reference=0.0): self.threshold=float(threshold); self.reference=float(reference); self.value=0.0
    def observe(self,x): self.value=max(0.0,self.value+float(x)-self.reference); return self.value + 1e-12 >= self.threshold
