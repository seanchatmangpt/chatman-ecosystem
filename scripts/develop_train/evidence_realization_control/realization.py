from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Realization:
    decision_id:str; evidence_id:str; observed_utility:float; observed_error:float; observed_cost:float
    def __post_init__(self):
        if not self.decision_id or not self.evidence_id: raise Refused('REFUSED[INVALID_REALIZATION]')
        if not (0<=self.observed_error<=1) or self.observed_cost<0: raise Refused('REFUSED[INVALID_REALIZATION]')
