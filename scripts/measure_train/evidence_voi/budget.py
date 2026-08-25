from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused

@dataclass(frozen=True)
class AcquisitionBudget:
    max_cost: Fraction
    max_latency_ms: int
    max_count: int
    def __post_init__(self):
        if not isinstance(self.max_cost, Fraction) or self.max_cost < 0 or self.max_latency_ms < 0 or self.max_count < 1:
            raise Refused("REFUSED[INVALID_ACQUISITION_BUDGET]")

def fits_budget(selected, candidate, budget):
    cost=sum((c.cost for c in selected), Fraction(0))+candidate.cost
    latency=max([c.latency_ms for c in selected]+[candidate.latency_ms])
    return cost <= budget.max_cost and latency <= budget.max_latency_ms and len(selected)+1 <= budget.max_count
