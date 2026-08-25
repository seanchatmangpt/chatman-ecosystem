from dataclasses import dataclass
from fractions import Fraction
from .evidence import ObservationEvidence
from .refusals import Refused

@dataclass(frozen=True)
class BudgetState:
    cost_remaining: Fraction
    latency_remaining: Fraction
    samples_remaining: int

    def __post_init__(self):
        if self.cost_remaining < 0 or self.latency_remaining < 0 or self.samples_remaining < 0:
            raise Refused("REFUSED_INVALID_BUDGET")

    def consume(self, evidence: ObservationEvidence) -> "BudgetState":
        if self.samples_remaining == 0 or evidence.realized_cost > self.cost_remaining or evidence.realized_latency > self.latency_remaining:
            raise Refused("REFUSED_BUDGET_EXCEEDED")
        return BudgetState(self.cost_remaining - evidence.realized_cost, self.latency_remaining - evidence.realized_latency, self.samples_remaining - 1)
