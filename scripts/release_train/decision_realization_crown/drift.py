from dataclasses import dataclass
from .domain import frac,positive
@dataclass(frozen=True)
class Cusum:
    value:object=0; threshold:object=1; slack:object=0
    def update(self,observed,target):
        v=frac(self.value); th=positive(self.threshold); s=frac(self.slack)
        nxt=max(frac(0),v+frac(observed)-frac(target)-s)
        return Cusum(nxt,th,s)
    @property
    def changed(self): return frac(self.value)>=positive(self.threshold)
