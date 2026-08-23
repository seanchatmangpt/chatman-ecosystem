from dataclasses import dataclass
from .refusals import Refused

@dataclass(frozen=True)
class CusumState:
    positive: float = 0.0
    negative: float = 0.0


def advance(state: CusumState, residual: float, *, allowance: float, threshold: float) -> CusumState:
    if allowance < 0 or threshold <= 0:
        raise Refused("REFUSED_INVALID_DRIFT_PARAMETERS")
    return CusumState(max(0.0, state.positive + residual - allowance), min(0.0, state.negative + residual + allowance))

def drifted(state: CusumState, threshold: float) -> bool:
    if threshold <= 0:
        raise Refused("REFUSED_INVALID_DRIFT_THRESHOLD")
    return state.positive > threshold or state.negative < -threshold
