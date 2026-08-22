from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json

_ALLOWED_PREDICTIONS = {"PASS", "FAIL"}


@dataclass(frozen=True, slots=True)
class CalibrationTrial:
    source_id: str
    truth_pass: bool
    predicted: str
    observed_at: datetime
    trial_id: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("REFUSED[EMPTY_CALIBRATION_SOURCE]")
        if self.predicted not in _ALLOWED_PREDICTIONS:
            raise ValueError("REFUSED[INVALID_CALIBRATION_PREDICTION]")
        if self.observed_at.tzinfo is None:
            raise ValueError("REFUSED[NAIVE_CALIBRATION_TIME]")
        canonical = json.dumps(
            {
                "source_id": self.source_id,
                "truth_pass": self.truth_pass,
                "predicted": self.predicted,
                "observed_at": self.observed_at.astimezone(timezone.utc).isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = sha256(canonical.encode()).hexdigest()
        if self.trial_id and self.trial_id != digest:
            raise ValueError("REFUSED[CALIBRATION_TRIAL_ID_MISMATCH]")
        object.__setattr__(self, "trial_id", digest)
