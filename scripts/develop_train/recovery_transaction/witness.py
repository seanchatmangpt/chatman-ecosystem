from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .context import RecoveryContext, digest_json
from .subject import Refusal

class WitnessKind(str, Enum):
    EXACT = "EXACT"
    SEMANTIC_EQUIVALENT = "SEMANTIC_EQUIVALENT"
    BACKWARD_COMPATIBLE = "BACKWARD_COMPATIBLE"

@dataclass(frozen=True)
class CompatibilityWitness:
    before_digest: str
    after_digest: str
    kind: WitnessKind
    proof_digest: str
    result: str = "PASS"
    def __post_init__(self) -> None:
        if self.result not in {"PASS", "FAIL", "PENDING", "UNKNOWN", "UNSUPPORTED"}:
            raise Refusal("INVALID_WITNESS_RESULT", self.result)
        if self.kind is WitnessKind.EXACT and self.before_digest != self.after_digest:
            raise Refusal("FALSE_EXACT_WITNESS", "EXACT requires identical context digests")
        if len(self.proof_digest) != 64:
            raise Refusal("INVALID_WITNESS_PROOF", "proof digest must be 64 hex chars")
    @classmethod
    def between(cls, before: RecoveryContext, after: RecoveryContext, kind: WitnessKind, proof: object):
        return cls(before.digest, after.digest, kind, digest_json(proof))
