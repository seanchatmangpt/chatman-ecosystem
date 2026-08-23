from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .errors import Refused
from .frontier import CalibrationFrontier
from .sensor_model import SensorCalibration
from .visibility import VisibilityObservation


@dataclass(frozen=True)
class AdmissionPolicy:
    min_support: int = 20
    min_wilson_lower: Fraction = Fraction(4, 5)
    max_false_current_rate: Fraction = Fraction(1, 20)
    max_false_stale_rate: Fraction = Fraction(1, 10)
    max_ambiguity_rate: Fraction = Fraction(1, 10)
    min_coverage: Fraction = Fraction(2, 3)
    max_replica_lag_seconds: int = 60

    def __post_init__(self) -> None:
        if self.min_support < 1 or self.max_replica_lag_seconds < 0:
            raise Refused("INVALID_ADMISSION_POLICY")


def admit_sensor(
    model: SensorCalibration,
    frontier: CalibrationFrontier,
    visibility: VisibilityObservation,
    policy: AdmissionPolicy,
) -> None:
    frontier.admits(model)
    if visibility.subject != model.subject:
        raise Refused("VISIBILITY_SUBJECT_MISMATCH")
    if model.support < policy.min_support:
        raise Refused("UNDER_SUPPORTED_QUORUM_SENSOR")
    if model.wilson_lower < policy.min_wilson_lower:
        raise Refused("UNRELIABLE_QUORUM_SENSOR")
    if model.false_current_rate > policy.max_false_current_rate:
        raise Refused("FALSE_CURRENT_RATE_EXCEEDED")
    if model.false_stale_rate > policy.max_false_stale_rate:
        raise Refused("FALSE_STALE_RATE_EXCEEDED")
    if model.ambiguity_rate > policy.max_ambiguity_rate:
        raise Refused("AMBIGUITY_RATE_EXCEEDED")
    if visibility.coverage < policy.min_coverage:
        raise Refused("INSUFFICIENT_REPLICA_VISIBILITY")
    if visibility.max_lag_seconds > policy.max_replica_lag_seconds:
        raise Refused("REPLICA_LAG_EXCEEDED")
