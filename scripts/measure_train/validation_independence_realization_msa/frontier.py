from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class IndependenceModel:
    generation:int; digest:str; state:str
    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_INDEPENDENCE_MODEL]")
def current(models):
    rows=tuple(models)
    if not rows: raise Refused("REFUSED[MISSING_INDEPENDENCE_MODEL]")
    g=max(m.generation for m in rows); latest=[m for m in rows if m.generation==g]
    if len({m.digest for m in latest})!=1: raise Refused("REFUSED[DIVERGENT_INDEPENDENCE_FRONTIER]")
    return latest[0]
