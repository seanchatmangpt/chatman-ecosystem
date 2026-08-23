from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class Budget:
    max_cost: Fraction
    max_latency_ms: Fraction
    max_samples: int
    max_steps: int

    def __post_init__(self):
        if min(self.max_cost,self.max_latency_ms) < 0 or min(self.max_samples,self.max_steps) < 0:
            raise Refused("REFUSED[INVALID_BUDGET]")

def budget_state(steps,budget):
    used_cost=sum((s.cost for s in steps), Fraction())
    used_latency=sum((s.latency_ms for s in steps), Fraction())
    used_samples=sum(s.samples for s in steps)
    exhausted=(used_cost>budget.max_cost or used_latency>budget.max_latency_ms
               or used_samples>budget.max_samples or len(steps)>budget.max_steps)
    return {"cost":used_cost,"latency_ms":used_latency,"samples":used_samples,
            "steps":len(steps),"exhausted":exhausted}
