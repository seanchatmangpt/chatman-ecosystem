from __future__ import annotations

from dataclasses import dataclass

from .errors import Refused
from .sensor_model import SensorCalibration
from .subject import Subject


@dataclass(frozen=True)
class CalibrationFrontier:
    subject: Subject
    generation: int
    calibration_digest: str

    @classmethod
    def from_models(cls, subject: Subject, models: list[SensorCalibration]) -> "CalibrationFrontier":
        current = [m for m in models if m.subject == subject]
        if not current:
            raise Refused("MISSING_CALIBRATION_FRONTIER", subject.canonical())
        generation = max(m.generation for m in current)
        maxima = [m for m in current if m.generation == generation]
        digests = {m.digest() for m in maxima}
        if len(digests) != 1:
            raise Refused("DIVERGENT_CALIBRATION_FRONTIER", str(generation))
        return cls(subject, generation, next(iter(digests)))

    def admits(self, model: SensorCalibration) -> None:
        if model.subject != self.subject:
            raise Refused("FOREIGN_CALIBRATION_SUBJECT")
        if model.generation != self.generation or model.digest() != self.calibration_digest:
            raise Refused("STALE_CALIBRATION_FRONTIER")
