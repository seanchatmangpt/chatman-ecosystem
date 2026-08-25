from dataclasses import dataclass
METHODOLOGIES=frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","object-centric","event-centric","declarative","procedural"})
@dataclass(frozen=True)
class Coverage:
    present:frozenset[str]
    @property
    def ratio(self): return len(self.present&METHODOLOGIES)/len(METHODOLOGIES)
    @property
    def complete(self): return METHODOLOGIES<=self.present
