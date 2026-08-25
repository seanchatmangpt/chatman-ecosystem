from dataclasses import dataclass
from fractions import Fraction
from .belief import BeliefState
from .budget import BudgetState
from .refusals import Refused

@dataclass(frozen=True)
class StopRule:
    confidence: Fraction
    max_steps: int

    def __post_init__(self):
        if self.confidence <= 0 or self.confidence > 1 or self.max_steps <= 0:
            raise Refused("REFUSED_INVALID_STOP_RULE")

    def should_stop(self, belief: BeliefState, budget: BudgetState, step: int) -> bool:
        return belief.confidence >= self.confidence or step >= self.max_steps or budget.samples_remaining == 0
