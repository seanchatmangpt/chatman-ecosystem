from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True, order=True)
class FederationModel:
    generation: int
    digest: str
    state: str

    def __post_init__(self):
        if self.generation < 0 or len(self.digest) != 64:
            raise Refused("REFUSED[INVALID_FEDERATION_MODEL]")

def current(models):
    rows = sorted(models, key=lambda model: model.generation)
    if not rows:
        return None
    top = rows[-1]
    peers = [row for row in rows if row.generation == top.generation]
    if any(row.digest != top.digest for row in peers):
        raise Refused("REFUSED[DIVERGENT_FEDERATION_FRONTIER]")
    return top
