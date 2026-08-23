from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True,order=True)
class TransportModel:
    source:str; target:str; generation:int; digest:str; calibrated:bool
    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_TRANSPORT_MODEL]")
def current(models):
    by={}
    for m in models:
        key=(m.source,m.target); old=by.get(key)
        if old is None or m.generation>old.generation:by[key]=m
        elif old.generation==m.generation and old.digest!=m.digest: raise Refused("REFUSED[DIVERGENT_TRANSPORT_FRONTIER]")
    return tuple(sorted(by.values()))
