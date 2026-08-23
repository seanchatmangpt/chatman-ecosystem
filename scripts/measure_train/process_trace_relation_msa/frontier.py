from dataclasses import dataclass
from .relation import Relation
from .subject import Refused

@dataclass(frozen=True, order=True)
class CalibrationFrontier:
    relation:Relation
    generation:int
    digest:str
    state:str
    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64:
            raise Refused("REFUSED[INVALID_CALIBRATION_FRONTIER]")

def current_frontier(rows):
    out={}
    for row in rows:
        old=out.get(row.relation)
        if old is None or row.generation>old.generation:
            out[row.relation]=row
        elif row.generation==old.generation and row.digest!=old.digest:
            raise Refused("REFUSED[DIVERGENT_RELATION_FRONTIER]")
    return tuple(sorted(out.values()))
