from enum import Enum
from dataclasses import dataclass
from .subject import Refused

class Selector(str, Enum):
    STRONGEST_DEFENSIBLE="STRONGEST_DEFENSIBLE"
    MINIMAX_ERROR="MINIMAX_ERROR"
    PARETO_ERROR_COST="PARETO_ERROR_COST"
    INFORMATION_GAIN="INFORMATION_GAIN"

@dataclass(frozen=True, order=True)
class SelectorIdentity:
    selector: Selector
    generation: int
    policy_digest: str

    def __post_init__(self):
        if self.generation < 0:
            raise Refused("REFUSED[INVALID_SELECTOR_GENERATION]")
        if len(self.policy_digest)!=64 or any(c not in "0123456789abcdef" for c in self.policy_digest):
            raise Refused("REFUSED[INVALID_SELECTOR_DIGEST]")
