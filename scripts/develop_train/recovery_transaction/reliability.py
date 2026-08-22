from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass(frozen=True)
class FailureModel:
    seed: int
    transient_probability: float
    max_retries: int
    def __post_init__(self) -> None:
        if not 0 <= self.transient_probability <= 1:
            raise ValueError("transient_probability must be in [0,1]")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
    def schedule(self) -> tuple[bool, ...]:
        rng = random.Random(self.seed)
        return tuple(rng.random() < self.transient_probability for _ in range(self.max_retries + 1))
    def first_success_attempt(self) -> int | None:
        for index, failed in enumerate(self.schedule()):
            if not failed:
                return index
        return None
