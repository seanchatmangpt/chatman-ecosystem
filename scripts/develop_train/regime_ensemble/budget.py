from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceBudget:
    maximum_samples: int
    maximum_detectors: int
    maximum_score_sum: float

    def __post_init__(self) -> None:
        if self.maximum_samples < 1 or self.maximum_detectors < 2 or self.maximum_score_sum <= 0:
            raise ValueError("REFUSED[INVALID_EVIDENCE_BUDGET]")

    def admit(self, sample_count: int, detector_count: int, score_sum: float) -> None:
        if sample_count > self.maximum_samples:
            raise ValueError("REFUSED[SAMPLE_BUDGET_EXCEEDED]")
        if detector_count > self.maximum_detectors:
            raise ValueError("REFUSED[DETECTOR_BUDGET_EXCEEDED]")
        if score_sum > self.maximum_score_sum:
            raise ValueError("REFUSED[SCORE_BUDGET_EXCEEDED]")
