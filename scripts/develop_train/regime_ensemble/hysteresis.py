from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class RegimeState(str, Enum):
    STABLE = "STABLE"
    SUSPECT = "SUSPECT"
    DRIFT = "DRIFT"

@dataclass(frozen=True)
class HysteresisState:
    state: RegimeState = RegimeState.STABLE
    change_streak: int = 0
    stable_streak: int = 0

def advance(current: HysteresisState, changed: bool, enter_after: int = 2, clear_after: int = 3) -> HysteresisState:
    if enter_after < 1 or clear_after < 1:
        raise ValueError("REFUSED[INVALID_HYSTERESIS_PARAMETERS]")
    if changed:
        cs = current.change_streak + 1
        state = RegimeState.DRIFT if cs >= enter_after else RegimeState.SUSPECT
        return HysteresisState(state, cs, 0)
    ss = current.stable_streak + 1
    if current.state is RegimeState.DRIFT and ss < clear_after:
        return HysteresisState(RegimeState.DRIFT, 0, ss)
    return HysteresisState(RegimeState.STABLE, 0, ss)
