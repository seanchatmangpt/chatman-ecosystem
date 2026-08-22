from __future__ import annotations
from dataclasses import dataclass
from .sample import ErrorSample, canonical_samples

@dataclass(frozen=True)
class SampleWindow:
    start: int
    stop: int
    minimum_support: int = 4

    def __post_init__(self) -> None:
        if self.start < 0 or self.stop <= self.start:
            raise ValueError("REFUSED[INVALID_HALF_OPEN_WINDOW]")
        if self.minimum_support < 2:
            raise ValueError("REFUSED[INVALID_SUPPORT_FLOOR]")

    def select(self, samples: list[ErrorSample]) -> tuple[ErrorSample, ...]:
        chosen = tuple(s for s in canonical_samples(samples) if self.start <= s.sequence < self.stop)
        if len(chosen) < self.minimum_support:
            raise ValueError("REFUSED[INSUFFICIENT_WINDOW_SUPPORT]")
        return chosen
