from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .drift import DriftKind
class CompatibilityKind(str,Enum):
    EXACT="EXACT"; SEMANTIC_EQUIVALENT="SEMANTIC_EQUIVALENT"; BACKWARD_COMPATIBLE="BACKWARD_COMPATIBLE"
@dataclass(frozen=True,slots=True)
class CompatibilityWitness:
    kind:CompatibilityKind; before_digest:str; after_digest:str; evidence_id:str
    def __post_init__(self)->None:
        if len(self.before_digest)!=64 or len(self.after_digest)!=64 or not self.evidence_id: raise ValueError("REFUSED[INVALID_COMPATIBILITY_WITNESS]")
        if self.kind is CompatibilityKind.EXACT and self.before_digest!=self.after_digest: raise ValueError("REFUSED[FALSE_EXACT_EQUIVALENCE]")
def admits_rebind(drift:DriftKind,witness:CompatibilityWitness|None)->bool:
    if drift is DriftKind.EXACT: return True
    return bool(witness and drift is DriftKind.POLICY and witness.kind is CompatibilityKind.SEMANTIC_EQUIVALENT)
