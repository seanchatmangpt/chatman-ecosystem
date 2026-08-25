from dataclasses import dataclass
from enum import Enum
from .refusal import require

class Methodology(str, Enum):
    DISCOVERY="DISCOVERY"
    CONFORMANCE="CONFORMANCE"
    SIMULATION="SIMULATION"
    PREDICTION="PREDICTION"
    OPTIMIZATION="OPTIMIZATION"
    INTERVENTION="INTERVENTION"
    MONITORING="MONITORING"
    EVENT_CENTRIC="EVENT_CENTRIC"
    OBJECT_CENTRIC="OBJECT_CENTRIC"
    DECLARATIVE="DECLARATIVE"
    PROCEDURAL="PROCEDURAL"

REQUIRED = frozenset(Methodology)

@dataclass(frozen=True)
class MethodologyCoverage:
    observed: frozenset[Methodology]

    def __post_init__(self):
        require(all(isinstance(x, Methodology) for x in self.observed), "UNKNOWN_METHODOLOGY")

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(sorted(x.value for x in REQUIRED - self.observed))

    @property
    def complete(self) -> bool:
        return not self.missing
