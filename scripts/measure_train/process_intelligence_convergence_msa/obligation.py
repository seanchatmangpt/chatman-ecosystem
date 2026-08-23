from dataclasses import dataclass
from .subject import Refused

STATES={"PASS","FAIL","UNKNOWN","UNSUPPORTED","REFUSED","BLOCKED"}

@dataclass(frozen=True, order=True)
class ObligationState:
    obligation_id: str
    state: str
    weight: int = 1
    def __post_init__(self):
        if not self.obligation_id: raise Refused("REFUSED[EMPTY_OBLIGATION]")
        if self.state not in STATES: raise Refused("REFUSED[INVALID_OBLIGATION_STATE]")
        if self.weight <= 0: raise Refused("REFUSED[INVALID_OBLIGATION_WEIGHT]")
