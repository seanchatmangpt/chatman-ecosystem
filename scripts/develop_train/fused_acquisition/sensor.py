from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
import re
from .calibration import Calibration
from .refusals import Refused

_ID = re.compile(r"^[A-Za-z0-9_.:-]+$")

@dataclass(frozen=True)
class Sensor:
    sensor_id: str
    family: str
    domain: str
    calibration: Calibration

    def __post_init__(self):
        if not all(_ID.fullmatch(x) for x in (self.sensor_id, self.family, self.domain)):
            raise Refused("INVALID_SENSOR_IDENTITY")

@dataclass(frozen=True)
class Observation:
    sensor_id: str
    generation: int
    verdict: str
    confidence: Fraction
    observed_at: datetime

    def __post_init__(self):
        if self.verdict not in {"CURRENT", "STALE", "AMBIGUOUS"}:
            raise Refused("INVALID_VERDICT")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("NAIVE_OBSERVATION_TIME")
        if self.observed_at > datetime.now(timezone.utc):
            raise Refused("FUTURE_OBSERVATION")
        q = self.confidence if isinstance(self.confidence, Fraction) else Fraction(self.confidence)
        if q < 0 or q > 1:
            raise Refused("INVALID_CONFIDENCE")
        object.__setattr__(self, "confidence", q)
