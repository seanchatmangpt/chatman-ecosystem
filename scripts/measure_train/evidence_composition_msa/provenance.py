from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class ProvenanceWitness:
    left: str
    right: str
    implementation_distinct: bool
    model_distinct: bool
    domain_distinct: bool
    def admit(self):
        if self.left == self.right: raise Refused("REFUSED[SELF_INDEPENDENCE]")
        if not (self.implementation_distinct and self.model_distinct and self.domain_distinct):
            raise Refused("REFUSED[UNPROVEN_EVIDENCE_INDEPENDENCE]")
        return True
