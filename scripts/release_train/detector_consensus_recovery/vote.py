from dataclasses import dataclass
from .subject import Subject
from .detector import DetectorIdentity

@dataclass(frozen=True)
class DetectorVote:
    subject: Subject
    detector: DetectorIdentity
    calibration_generation: int
    calibration_fingerprint: str
    verdict: str
    score_milli: int
    def __post_init__(self):
        if self.verdict not in {"STABLE","DRIFT","UNKNOWN","FAIL"}: raise ValueError("REFUSED[INVALID_VOTE]")
        if self.calibration_generation < 1 or not (0 <= self.score_milli <= 1000): raise ValueError("REFUSED[INVALID_VOTE_BOUND]")
