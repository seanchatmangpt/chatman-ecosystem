from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True, order=True)
class KineticsModel:
    generation: int
    digest: str
    state: str

    def __post_init__(self):
        if self.generation < 0 or len(self.digest) != 64:
            raise Refused("INVALID_KINETICS_MODEL")
        if self.state not in {"CALIBRATED", "INSUFFICIENT", "UNRELIABLE"}:
            raise Refused("INVALID_MODEL_STATE")

def current(models):
    rows = tuple(models)
    if not rows:
        raise Refused("EMPTY_MODEL_FRONTIER")
    generation = max(model.generation for model in rows)
    newest = [model for model in rows if model.generation == generation]
    if len({model.digest for model in newest}) != 1:
        raise Refused("DIVERGENT_CURRENT_KINETICS_MODEL")
    return sorted(newest)[0]
