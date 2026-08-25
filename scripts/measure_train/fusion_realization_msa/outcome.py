from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
@dataclass(frozen=True, order=True)
class SensorOutcome:
    subject: Subject
    plan_id: str
    sensor_id: str
    evidence_id: str
    distribution: tuple[float,...]
    case_ids: tuple[str,...]
    cost: float
    latency_ms: int
    observed_at: datetime
    def __post_init__(self):
        if not all(x.strip() for x in (self.plan_id,self.sensor_id,self.evidence_id)): raise Refused("REFUSED[INVALID_OUTCOME_IDENTITY]")
        if self.cost < 0 or self.latency_ms < 0: raise Refused("REFUSED[INVALID_OUTCOME_COST]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_OUTCOME_TIME]")
