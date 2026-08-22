from dataclasses import dataclass
from datetime import datetime, timezone

STRATEGIES={"MAX_INFORMATION_GAIN","MAX_INFORMATION_PER_COST","MIN_EXPECTED_ENTROPY"}

@dataclass(frozen=True)
class Realization:
    strategy: str
    predicted_gain: float
    realized_gain: float
    planned_cost: float
    actual_cost: float
    planned_latency: float
    actual_latency: float
    failed: bool
    observed_at: datetime
    def __post_init__(self):
        if self.strategy not in STRATEGIES:
            raise ValueError("REFUSED[UNKNOWN_STRATEGY]")
        if self.observed_at.tzinfo is None or self.observed_at > datetime.now(timezone.utc):
            raise ValueError("REFUSED[INVALID_REALIZATION_TIME]")
        values=(self.predicted_gain,self.realized_gain,self.planned_cost,self.actual_cost,self.planned_latency,self.actual_latency)
        if any(v < 0 for v in values) or self.planned_cost == 0 or self.planned_latency == 0:
            raise ValueError("REFUSED[INVALID_REALIZATION]")
    @property
    def utility(self):
        risk=1.0 if self.failed else 0.0
        return self.realized_gain - (self.actual_cost/self.planned_cost-1.0) - (self.actual_latency/self.planned_latency-1.0) - risk
    @property
    def residual(self):
        return self.realized_gain-self.predicted_gain
