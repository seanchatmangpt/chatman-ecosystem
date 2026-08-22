from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True, order=True)
class ErrorSample:
    sequence: int
    error: float
    detector_domain: str

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("REFUSED[NEGATIVE_SEQUENCE]")
        if not isfinite(self.error) or not 0.0 <= self.error <= 1.0:
            raise ValueError("REFUSED[INVALID_ERROR_SAMPLE]")
        if not self.detector_domain.strip():
            raise ValueError("REFUSED[EMPTY_DETECTOR_DOMAIN]")

def canonical_samples(samples: list[ErrorSample]) -> tuple[ErrorSample, ...]:
    ordered = tuple(sorted(samples, key=lambda s: s.sequence))
    if len({s.sequence for s in ordered}) != len(ordered):
        raise ValueError("REFUSED[DUPLICATE_SAMPLE_SEQUENCE]")
    return ordered
