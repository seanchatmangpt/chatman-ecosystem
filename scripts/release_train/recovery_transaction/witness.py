from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
from .subject import Refusal
_HEX64=re.compile(r"^[0-9a-f]{64}$")
class WitnessKind(str, Enum):
    EXACT="EXACT"; SEMANTIC_EQUIVALENT="SEMANTIC_EQUIVALENT"; BACKWARD_COMPATIBLE="BACKWARD_COMPATIBLE"
@dataclass(frozen=True)
class CompatibilityWitness:
    before_digest: str
    after_digest: str
    kind: WitnessKind
    proof_digest: str
    passed: bool
    def __post_init__(self) -> None:
        if not all(_HEX64.fullmatch(x) for x in (self.before_digest,self.after_digest,self.proof_digest)):
            raise Refusal("REFUSED[INVALID_COMPATIBILITY_WITNESS]")
        if self.kind is WitnessKind.EXACT and self.before_digest != self.after_digest:
            raise Refusal("REFUSED[FALSE_EXACT_WITNESS]")
