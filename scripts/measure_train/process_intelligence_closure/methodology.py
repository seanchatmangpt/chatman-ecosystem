from dataclasses import dataclass
from .subject import Refused

REQUIRED=frozenset({"DISCOVERY","CONFORMANCE","SIMULATION","PREDICTION","OPTIMIZATION","INTERVENTION","MONITORING","OBJECT_CENTRIC","EVENT_CENTRIC","DECLARATIVE","PROCEDURAL"})

@dataclass(frozen=True)
class MethodologyCoverage:
    capabilities: frozenset[str]
    def __post_init__(self):
        unknown=set(self.capabilities)-REQUIRED
        if unknown: raise Refused("REFUSED[UNKNOWN_METHODOLOGY]")
    @property
    def missing(self): return tuple(sorted(REQUIRED-self.capabilities))
    @property
    def complete(self): return not self.missing
