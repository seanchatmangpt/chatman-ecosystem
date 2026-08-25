from dataclasses import dataclass
from fractions import Fraction
from .budget import BudgetState
from .refusals import Refused

@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    sensor_id: str
    predicted_information_bits: float
    independence_gain: Fraction
    cost: Fraction
    latency: Fraction
    uncertainty: float = 0.0


def select(candidates: list[Candidate], budget: BudgetState, strategy: str) -> Candidate:
    allowed = [c for c in candidates if c.cost <= budget.cost_remaining and c.latency <= budget.latency_remaining and budget.samples_remaining > 0]
    if not allowed:
        raise Refused("REFUSED_NO_ADMITTED_CANDIDATE")
    keys = {
        "MAX_INFORMATION": lambda c: (c.predicted_information_bits, c.independence_gain, -float(c.cost), c.candidate_id),
        "INFORMATION_PER_COST": lambda c: (c.predicted_information_bits / max(float(c.cost), 1e-12), c.independence_gain, c.candidate_id),
        "MAX_INDEPENDENCE": lambda c: (c.independence_gain, c.predicted_information_bits, c.candidate_id),
        "UCB_DISCOVERY": lambda c: (c.predicted_information_bits + c.uncertainty, c.independence_gain, c.candidate_id),
        "MINIMAX_LATENCY": lambda c: (-float(c.latency), c.predicted_information_bits, c.candidate_id),
    }
    if strategy not in keys:
        raise Refused("REFUSED_UNKNOWN_ACQUISITION_STRATEGY")
    return max(allowed, key=keys[strategy])
