from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class RealizationModel:
    generation: int
    digest: str
    calibration_admitted: bool
    drifted: bool

def current(models):
    if not models:
        raise Refused("NO_REALIZATION_MODEL")
    g=max(m.generation for m in models)
    xs=[m for m in models if m.generation==g]
    if len({m.digest for m in xs}) != 1:
        raise Refused("SPLIT_REALIZATION_FRONTIER")
    return xs[0]
