from dataclasses import dataclass
from fractions import Fraction
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class AcquisitionBudget:
    max_cost:Fraction; max_latency_ms:int; max_count:int
    def __post_init__(self):
        if self.max_cost<0 or self.max_latency_ms<0 or self.max_count<1: raise Refusal('REFUSED_INVALID_ACQUISITION_BUDGET')
    def admits(self,selected):
        return len(selected)<=self.max_count and sum((c.cost for c in selected),Fraction())<=self.max_cost and sum(c.latency_ms for c in selected)<=self.max_latency_ms
