from dataclasses import dataclass
from enum import Enum
from .errors import Refused
class State(str, Enum):
    UNKNOWN="UNKNOWN"; PASS="PASS"; FAIL="FAIL"; BLOCKED="BLOCKED"; UNSUPPORTED="UNSUPPORTED"; REFUSED="REFUSED"
@dataclass(frozen=True)
class Obligation:
    key: str
    state: State
    source: str
    def __post_init__(self):
        if not self.key or not self.source: raise Refused("REFUSED[INVALID_OBLIGATION]")
