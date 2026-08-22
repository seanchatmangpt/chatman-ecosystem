from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .subject import Refusal
from .trials import CalibrationTrial

@dataclass(frozen=True, slots=True)
class CalibrationWindow:
    start: datetime
    end: datetime
    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None: raise Refusal("REFUSED[NAIVE_CALIBRATION_WINDOW]")
        if self.end <= self.start: raise Refusal("REFUSED[INVALID_CALIBRATION_WINDOW]")
    def select(self,trials:tuple[CalibrationTrial,...],*,source_id:str)->tuple[CalibrationTrial,...]:
        return tuple(t for t in trials if t.source_id==source_id and self.start<=t.observed_at<self.end)
