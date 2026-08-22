from __future__ import annotations
from dataclasses import dataclass
from random import Random
@dataclass(frozen=True, slots=True)
class AdvanceFault:
    producer_repository: str
    delta: int = 1
def deterministic_advancement(repositories: tuple[str, ...], *, seed: int, count: int = 1) -> tuple[AdvanceFault, ...]:
    if count <= 0 or not repositories: return ()
    rng = Random(seed); ordered = tuple(sorted(repositories))
    return tuple(AdvanceFault(rng.choice(ordered)) for _ in range(count))
