from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True,order=True)
class CapitalModel:
    model_id:str; generation:int; digest:str; state:str
    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_MODEL]")
def current(models):
    by={}
    for m in models:
        old=by.get(m.model_id)
        if old is None or m.generation>old.generation: by[m.model_id]=m
        elif m.generation==old.generation and m.digest!=old.digest: raise Refused("REFUSED[DIVERGENT_CAPITAL_FRONTIER]")
    return tuple(sorted(by.values()))
