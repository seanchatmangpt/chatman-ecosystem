from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True, order=True)
class PolicyCalibration:
    strategy: str
    generation: int
    calibration_state: str
    support: int
    mae: float


def current_frontier(rows):
    current={}
    for row in rows:
        old=current.get(row.strategy)
        if old is None or row.generation>old.generation:
            current[row.strategy]=row
        elif row.generation==old.generation and row!=old:
            raise Refused("REFUSED[DIVERGENT_POLICY_CALIBRATION]")
    return tuple(sorted(current.values()))
