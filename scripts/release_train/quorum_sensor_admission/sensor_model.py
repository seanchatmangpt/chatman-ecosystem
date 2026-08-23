from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json

from .errors import Refused
from .subject import Subject


def _rate(value: Fraction, name: str) -> Fraction:
    if value < 0 or value > 1:
        raise Refused("INVALID_RATE", name)
    return value


@dataclass(frozen=True)
class SensorCalibration:
    subject: Subject
    generation: int
    support: int
    false_current_rate: Fraction
    false_stale_rate: Fraction
    ambiguity_rate: Fraction
    wilson_lower: Fraction
    detector_family: str

    def __post_init__(self) -> None:
        if self.generation < 1 or self.support < 0:
            raise Refused("INVALID_CALIBRATION_CARDINALITY")
        if not self.detector_family.strip():
            raise Refused("MISSING_DETECTOR_FAMILY")
        for value, name in [
            (self.false_current_rate, "false_current_rate"),
            (self.false_stale_rate, "false_stale_rate"),
            (self.ambiguity_rate, "ambiguity_rate"),
            (self.wilson_lower, "wilson_lower"),
        ]:
            _rate(value, name)

    def payload(self) -> dict[str, object]:
        def f(v: Fraction) -> list[int]:
            return [v.numerator, v.denominator]

        return {
            "subject": self.subject.canonical(),
            "generation": self.generation,
            "support": self.support,
            "false_current_rate": f(self.false_current_rate),
            "false_stale_rate": f(self.false_stale_rate),
            "ambiguity_rate": f(self.ambiguity_rate),
            "wilson_lower": f(self.wilson_lower),
            "detector_family": self.detector_family,
        }

    def digest(self) -> str:
        body = json.dumps(self.payload(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(body).hexdigest()
