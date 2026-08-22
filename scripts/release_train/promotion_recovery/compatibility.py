from dataclasses import dataclass
from enum import Enum
from .subject import Refusal
class CompatibilityKind(str,Enum):
    EXACT='EXACT'; SEMANTIC_EQUIVALENT='SEMANTIC_EQUIVALENT'; BACKWARD_COMPATIBLE='BACKWARD_COMPATIBLE'
@dataclass(frozen=True)
class CompatibilityWitness:
    kind: CompatibilityKind
    before_fingerprint: str
    after_fingerprint: str
    evidence_id: str
    def __post_init__(self):
        if not self.evidence_id or len(self.before_fingerprint)!=64 or len(self.after_fingerprint)!=64:
            raise Refusal('REFUSED[INVALID_COMPATIBILITY_WITNESS]')
        if self.kind is CompatibilityKind.EXACT and self.before_fingerprint!=self.after_fingerprint:
            raise Refusal('REFUSED[FALSE_EXACT_COMPATIBILITY]')
