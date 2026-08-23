from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from .errors import Refused
class HorizonState(StrEnum):
    READY="READY"; ACQUIRING="ACQUIRING"; SATISFIED="SATISFIED"; EXHAUSTED="EXHAUSTED"; DRIFTED="DRIFTED"; BLOCKED="BLOCKED"; STALE="STALE"
@dataclass(frozen=True)
class HorizonPolicy:
    max_steps:int; confidence:Fraction; max_information_debt:Fraction; max_cost_slip:Fraction; max_latency_slip:Fraction
    def __post_init__(self):
        if self.max_steps<=0: raise Refused("INVALID_HORIZON")
        if not 0<self.confidence<=1: raise Refused("INVALID_CONFIDENCE")
        if min(self.max_information_debt,self.max_cost_slip,self.max_latency_slip)<0: raise Refused("INVALID_DEBT_LIMIT")
