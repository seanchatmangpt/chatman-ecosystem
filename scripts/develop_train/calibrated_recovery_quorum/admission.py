from __future__ import annotations

from datetime import datetime

from .calibration_model import CalibrationModel
from .witness import RecoveryWitness


def admit_witness(
    witness: RecoveryWitness,
    *,
    attempt_id: str,
    now: datetime,
    calibration: CalibrationModel,
    min_trials: int,
) -> tuple[bool, str | None]:
    if now.tzinfo is None:
        raise ValueError("REFUSED[NAIVE_ADMISSION_TIME]")
    if witness.attempt_id != attempt_id:
        return False, "REFUSED[FOREIGN_RECOVERY_ATTEMPT]"
    if witness.observed_at > now:
        return False, "REFUSED[FUTURE_EVIDENCE]"
    if calibration.source_id != witness.source_fingerprint:
        return False, "REFUSED[CALIBRATION_SOURCE_MISMATCH]"
    if calibration.support < min_trials:
        return False, "REFUSED[UNDER_CALIBRATED_SOURCE]"
    return True, None
