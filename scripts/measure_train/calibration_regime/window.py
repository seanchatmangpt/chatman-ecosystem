from dataclasses import dataclass
from datetime import datetime
from .subject import Refused

@dataclass(frozen=True, order=True)
class CalibrationWindow:
    start: datetime
    end: datetime
    min_trials: int = 4
    def __post_init__(self):
        if self.start.tzinfo is None or self.end.tzinfo is None: raise Refused("REFUSED[NAIVE_WINDOW]")
        if self.end <= self.start: raise Refused("REFUSED[INVALID_WINDOW]")
        if self.min_trials < 1: raise Refused("REFUSED[INVALID_MIN_TRIALS]")
    def select(self, trials):
        return tuple(t for t in trials if self.start <= t.observed_at < self.end)
    def standing(self, trials):
        return "SUPPORTED" if len(self.select(trials)) >= self.min_trials else "INSUFFICIENT"
