from dataclasses import dataclass
from datetime import datetime
from .subject import Refused

@dataclass(frozen=True, order=True)
class CutCandidate:
    cut_id:str
    generation:int
    producer_generations:tuple
    observed_at:datetime
    complete:bool=True
    def __post_init__(self):
        if not self.cut_id.strip(): raise Refused("REFUSED[EMPTY_CUT_ID]")
        if self.generation < 0: raise Refused("REFUSED[INVALID_CUT_GENERATION]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_CUT_TIME]")
        repos=[r for r,g in self.producer_generations]
        if len(repos)!=len(set(repos)): raise Refused("REFUSED[DUPLICATE_CUT_PRODUCER]")
        if any(g<0 for _,g in self.producer_generations): raise Refused("REFUSED[INVALID_PRODUCER_GENERATION]")
