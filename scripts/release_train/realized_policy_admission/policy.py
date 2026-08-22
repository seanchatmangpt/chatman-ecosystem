from dataclasses import dataclass
import hashlib, json

STRATEGIES=("MAX_INFORMATION_GAIN","MAX_INFORMATION_PER_COST","MIN_EXPECTED_ENTROPY")

@dataclass(frozen=True)
class Policy:
    generation: int
    min_support: int
    max_failure_rate: float
    max_cost_ratio: float
    max_latency_ratio: float
    drift_threshold: float
    def __post_init__(self):
        if self.generation < 1 or self.min_support < 1:
            raise ValueError("REFUSED[INVALID_POLICY]")
        if not (0 <= self.max_failure_rate <= 1) or min(self.max_cost_ratio,self.max_latency_ratio,self.drift_threshold) <= 0:
            raise ValueError("REFUSED[INVALID_POLICY]")
    @property
    def digest(self):
        body={"generation":self.generation,"min_support":self.min_support,"max_failure_rate":self.max_failure_rate,
              "max_cost_ratio":self.max_cost_ratio,"max_latency_ratio":self.max_latency_ratio,"drift_threshold":self.drift_threshold}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
