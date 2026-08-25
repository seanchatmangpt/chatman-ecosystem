from dataclasses import dataclass
from .refusal import Refused

FAMILIES={"IPS","SNIPS","CLIPPED_IPS","DIRECT_MODEL","DOUBLY_ROBUST"}
@dataclass(frozen=True, order=True)
class EstimatorIdentity:
    estimator_id: str
    family: str
    implementation_digest: str
    model_digest: str | None = None
    def __post_init__(self):
        if not self.estimator_id.strip() or self.family not in FAMILIES:
            raise Refused("REFUSED[INVALID_ESTIMATOR_IDENTITY]")
        if len(self.implementation_digest)!=64 or any(c not in "0123456789abcdef" for c in self.implementation_digest):
            raise Refused("REFUSED[INVALID_IMPLEMENTATION_DIGEST]")
        if self.family in {"DIRECT_MODEL","DOUBLY_ROBUST"} and (self.model_digest is None or len(self.model_digest)!=64):
            raise Refused("REFUSED[MISSING_MODEL_PROVENANCE]")
