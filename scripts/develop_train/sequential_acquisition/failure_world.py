from dataclasses import dataclass
import hashlib
from .refusals import Refused

@dataclass(frozen=True)
class FailureWorld:
    seed: str
    dropped_sensor: str | None
    correlated_pair: tuple[str, str] | None

def world(seed: str, sensors: list[str]) -> FailureWorld:
    if not seed or not sensors or len(set(sensors)) != len(sensors):
        raise Refused("REFUSED_INVALID_FAILURE_WORLD")
    ordered = sorted(sensors)
    h = hashlib.sha256(seed.encode()).digest()
    drop = ordered[h[0] % len(ordered)] if h[1] % 3 == 0 else None
    pair = None
    if len(ordered) >= 2 and h[2] % 2 == 0:
        i = h[3] % len(ordered); j = h[4] % len(ordered)
        if i == j: j = (j + 1) % len(ordered)
        pair = tuple(sorted((ordered[i], ordered[j])))
    return FailureWorld(seed, drop, pair)
