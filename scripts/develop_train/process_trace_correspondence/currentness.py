from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Currentness:
    generation:int; observed_at:int; expires_at:int
    def admits(self,now): return self.generation>=0 and self.observed_at<=now<self.expires_at
def require_current(items,now):
    if not items: raise Refused("NO_CURRENTNESS")
    gs={x.generation for x in items}
    if len(gs)!=1: raise Refused("GENERATION_DIVERGENCE")
    if not all(x.admits(now) for x in items): raise Refused("STALE_EVIDENCE")
    return next(iter(gs))
