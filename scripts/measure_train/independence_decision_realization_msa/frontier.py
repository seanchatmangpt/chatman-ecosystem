from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True, order=True)
class PolicyModel:
    policy_id:str; generation:int; digest:str; state:str
    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_POLICY_MODEL]")
def current_frontier(models):
    by={}
    for m in models:
        old=by.get(m.policy_id)
        if old is None or m.generation>old.generation: by[m.policy_id]=m
        elif m.generation==old.generation and m.digest!=old.digest: raise Refused("REFUSED[DIVERGENT_POLICY_FRONTIER]")
    return tuple(sorted(by.values()))
