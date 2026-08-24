from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Calibration:
    generation: int
    digest: str
    support: int
    mae: float

    def admitted(self, minimum_support=5, maximum_mae=0.2):
        return self.support >= minimum_support and self.mae <= maximum_mae

def current(calibrations):
    values = tuple(calibrations)
    if not values:
        raise Refused("NO_CALIBRATION")
    generation = max(item.generation for item in values)
    latest = [item for item in values if item.generation == generation]
    if len({item.digest for item in latest}) != 1:
        raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    return latest[0]
