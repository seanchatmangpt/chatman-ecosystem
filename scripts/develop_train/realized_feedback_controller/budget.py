from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class FeedbackBudget:
    max_transitions: int
    max_exploration_cost: Fraction

    def admits(self, transitions: int, exploration_cost: Fraction):
        if transitions < 0 or exploration_cost < 0:
            raise Refused("REFUSED_INVALID_FEEDBACK_BUDGET")
        return transitions < self.max_transitions and exploration_cost <= self.max_exploration_cost
