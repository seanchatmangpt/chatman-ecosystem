from dataclasses import dataclass
from .policy import STRATEGIES

@dataclass(frozen=True)
class Score:
    strategy: str
    value: float
    support: int

def score(strategy, *, lower_utility, realized_gain, cost_ratio, expected_entropy):
    if strategy not in STRATEGIES: raise ValueError("REFUSED[UNKNOWN_STRATEGY]")
    if strategy=="MAX_INFORMATION_GAIN": return realized_gain
    if strategy=="MAX_INFORMATION_PER_COST": return realized_gain/max(cost_ratio,1e-12)
    return -expected_entropy

def select(scores):
    if not scores: raise ValueError("REFUSED[NO_ADMITTED_STRATEGY]")
    return sorted(scores,key=lambda s:(-s.value,-s.support,s.strategy))[0]
