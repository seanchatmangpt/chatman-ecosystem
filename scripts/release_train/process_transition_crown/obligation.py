from dataclasses import dataclass
from enum import Enum
from .refusal import Refused

class State(str, Enum):
    UNKNOWN="UNKNOWN"; PARTIAL_ALIVE="PARTIAL_ALIVE"; ALIVE="ALIVE"; BLOCKED="BLOCKED"; BUILD_BROKEN="BUILD_BROKEN"; UNSUPPORTED="UNSUPPORTED"

@dataclass(frozen=True)
class Obligation:
    key: str
    state: State
    source: str

    def __post_init__(self) -> None:
        if not self.key or not self.source:
            raise Refused("INVALID_OBLIGATION")
