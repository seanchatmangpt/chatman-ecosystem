from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True, order=True)
class DependenceModel:
    pair_key:str
    generation:int
    digest:str
    calibration_state:str

    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64:
            raise Refused("REFUSED[INVALID_DEPENDENCE_MODEL]")

def current_frontier(models):
    by={}
    for model in models:
        old=by.get(model.pair_key)
        if old is None or model.generation>old.generation:
            by[model.pair_key]=model
        elif model.generation==old.generation and model.digest!=old.digest:
            raise Refused("REFUSED[DIVERGENT_DEPENDENCE_FRONTIER]")
    return tuple(sorted(by.values()))
