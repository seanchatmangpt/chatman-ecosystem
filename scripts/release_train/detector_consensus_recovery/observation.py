from dataclasses import dataclass
from datetime import datetime
from .subject import Subject
from .detector import DetectorIdentity

@dataclass(frozen=True)
class DetectorObservation:
    subject: Subject
    detector: DetectorIdentity
    case_id: str
    observed_at: datetime
    expected_drift: bool
    detected_drift: bool
    delay_steps: int | None = None
    def __post_init__(self):
        if not self.case_id: raise ValueError("REFUSED[MISSING_CASE_ID]")
        if self.delay_steps is not None and self.delay_steps < 0: raise ValueError("REFUSED[NEGATIVE_DELAY]")
