from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
@dataclass(frozen=True, order=True)
class FusionPlan:
    subject: Subject
    plan_id: str
    frontier_digest: str
    sensor_ids: tuple[str,...]
    predicted_gain_bits: float
    max_cost: float
    max_latency_ms: int
    issued_at: datetime
    def __post_init__(self):
        if not self.plan_id.strip(): raise Refused("REFUSED[EMPTY_PLAN_ID]")
        if len(self.frontier_digest)!=64: raise Refused("REFUSED[INVALID_FRONTIER_DIGEST]")
        if len(set(self.sensor_ids))!=len(self.sensor_ids) or not self.sensor_ids: raise Refused("REFUSED[INVALID_SENSOR_SET]")
        if self.predicted_gain_bits < 0 or self.max_cost < 0 or self.max_latency_ms < 0: raise Refused("REFUSED[INVALID_PLAN_BOUNDS]")
        if self.issued_at.tzinfo is None or self.issued_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_PLAN_TIME]")
