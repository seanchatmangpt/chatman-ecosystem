from dataclasses import dataclass
from datetime import datetime, timezone
from .errors import Refused
from .rational import unit
from .sensor import SensorIdentity
from .subject import Subject

@dataclass(frozen=True)
class Observation:
    subject: Subject
    sensor: SensorIdentity
    verdict: str
    confidence: object
    observed_at: datetime
    evidence_id: str
    def __post_init__(self):
        if self.sensor.subject != self.subject:
            raise Refused("FOREIGN_SENSOR")
        if self.verdict not in {"CURRENT", "STALE", "AMBIGUOUS"}:
            raise Refused("INVALID_SENSOR_VERDICT")
        object.__setattr__(self, "confidence", unit(self.confidence))
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("NAIVE_OBSERVATION_TIME")
        if not self.evidence_id:
            raise Refused("MISSING_EVIDENCE_ID")
    def require_current(self, now: datetime, max_age_seconds: int):
        if now.tzinfo is None or now.utcoffset() is None:
            raise Refused("NAIVE_NOW")
        age = (now.astimezone(timezone.utc) - self.observed_at.astimezone(timezone.utc)).total_seconds()
        if age < 0:
            raise Refused("FUTURE_OBSERVATION")
        if age > max_age_seconds:
            raise Refused("STALE_OBSERVATION")
