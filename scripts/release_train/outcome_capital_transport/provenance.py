from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class EvidenceNode:
    evidence_id: str
    implementation: str
    model: str
    domain: str
    parents: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.evidence_id or not self.implementation or not self.model or not self.domain:
            raise Refused("INCOMPLETE_PROVENANCE")
        if self.evidence_id in self.parents:
            raise Refused("SELF_ANCESTRY", self.evidence_id)

def distinct(a: EvidenceNode, b: EvidenceNode):
    return all(x != y for x, y in ((a.implementation,b.implementation),(a.model,b.model),(a.domain,b.domain)))
