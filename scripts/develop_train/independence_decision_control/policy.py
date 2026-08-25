from dataclasses import dataclass
from enum import Enum
from fractions import Fraction


class Strategy(str, Enum):
    MIN_EXPECTED_LOSS = "MIN_EXPECTED_LOSS"
    MIN_FALSE_INDEPENDENT = "MIN_FALSE_INDEPENDENT"
    MAX_INFORMATION_VALUE = "MAX_INFORMATION_VALUE"
    ROBUST_DEFER = "ROBUST_DEFER"


@dataclass(frozen=True)
class Candidate:
    name: str
    expected_loss: Fraction
    false_independent: Fraction
    information_value: Fraction
    drift_risk: Fraction
    decision: str


def select(candidates, strategy):
    if strategy is Strategy.MIN_EXPECTED_LOSS:
        return min(candidates, key=lambda item: (item.expected_loss, item.name))
    if strategy is Strategy.MIN_FALSE_INDEPENDENT:
        return min(candidates, key=lambda item: (item.false_independent, item.name))
    if strategy is Strategy.MAX_INFORMATION_VALUE:
        return max(candidates, key=lambda item: (item.information_value, item.name))
    return min(candidates, key=lambda item: (0 if item.decision == "DEFER" else 1, item.drift_risk, item.name))
