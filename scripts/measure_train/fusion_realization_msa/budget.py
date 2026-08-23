from dataclasses import dataclass
@dataclass(frozen=True)
class BudgetRealization:
    total_cost: float
    max_latency_ms: int
    cost_slip: float
    latency_slip_ms: int
    within_budget: bool
def realize_budget(plan,outcomes):
    cost=sum(o.cost for o in outcomes); latency=max((o.latency_ms for o in outcomes),default=0)
    return BudgetRealization(cost,latency,cost-plan.max_cost,latency-plan.max_latency_ms,cost<=plan.max_cost and latency<=plan.max_latency_ms)
