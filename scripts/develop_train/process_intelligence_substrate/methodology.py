from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .errors import Refused

class Methodology(str, Enum):
    DISCOVERY="DISCOVERY"; CONFORMANCE="CONFORMANCE"; SIMULATION="SIMULATION"; PREDICTION="PREDICTION"; OPTIMIZATION="OPTIMIZATION"; INTERVENTION="INTERVENTION"; MONITORING="MONITORING"

@dataclass(frozen=True)
class MethodologySet:
    observed: frozenset[Methodology]

    def missing(self, required: frozenset[Methodology]) -> frozenset[Methodology]:
        return required - self.observed

    def require(self, required: frozenset[Methodology]) -> None:
        missing = self.missing(required)
        if missing:
            raise Refused("METHODOLOGY_CLOSURE", ",".join(sorted(x.value for x in missing)))
