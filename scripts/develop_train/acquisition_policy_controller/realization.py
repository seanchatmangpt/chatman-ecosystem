from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from .subject import Refusal, Subject
STRATEGIES=("MAX_INFORMATION_GAIN","MAX_INFORMATION_PER_COST","MIN_EXPECTED_ENTROPY")
@dataclass(frozen=True, slots=True)
class Realization:
    subject:Subject
    plan_id:str
    candidate_id:str
    strategy:str
    policy_generation:int
    predicted_gain:float
    realized_gain:float
    planned_cost:float
    actual_cost:float
    planned_latency_ms:float
    actual_latency_ms:float
    observed_at:datetime
    outcome:str
    def __post_init__(self):
        vals=(self.predicted_gain,self.realized_gain,self.planned_cost,self.actual_cost,self.planned_latency_ms,self.actual_latency_ms)
        if self.strategy not in STRATEGIES: raise Refusal("REFUSED_UNKNOWN_STRATEGY")
        if self.policy_generation<0 or any(not isfinite(x) for x in vals) or min(vals)<0: raise Refusal("REFUSED_INVALID_REALIZATION")
        if self.observed_at.tzinfo is None: raise Refusal("REFUSED_NAIVE_TIME")
        if self.observed_at>datetime.now(timezone.utc): raise Refusal("REFUSED_FUTURE_REALIZATION")
        if self.outcome not in {"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}: raise Refusal("REFUSED_INVALID_OUTCOME")
