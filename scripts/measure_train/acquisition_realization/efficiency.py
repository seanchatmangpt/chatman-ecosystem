from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused

@dataclass(frozen=True)
class ResourceEfficiency:
    gain_per_cost: float
    gain_per_second: float
    cost_ratio: Fraction
    latency_ratio: Fraction


def evaluate(plan, outcome, realized_gain: float) -> ResourceEfficiency:
    if plan.cost <= 0:
        raise Refused("REFUSED[INVALID_PLANNED_COST]")
    seconds=max(outcome.actual_latency_ms,1)/1000.0
    cost=max(float(outcome.actual_cost),1e-12)
    planned_latency=max(plan.latency_ms,1)
    return ResourceEfficiency(
        gain_per_cost=realized_gain/cost,
        gain_per_second=realized_gain/seconds,
        cost_ratio=outcome.actual_cost/plan.cost,
        latency_ratio=Fraction(outcome.actual_latency_ms,planned_latency),
    )
