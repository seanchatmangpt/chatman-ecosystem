from dataclasses import dataclass
from .subject import Refused

KINDS={"WORKFLOW","RUNTIME","ARTIFACT","RECEIPT","STATUS","HUMAN_ATTESTATION"}

@dataclass(frozen=True, order=True)
class EvidenceSource:
    kind: str
    producer: str
    run_id: str
    artifact_digest: str
    source_id: str
    def __post_init__(self):
        if self.kind not in KINDS:
            raise Refused("REFUSED[UNKNOWN_SOURCE_KIND]")
        if not self.producer.strip() or not self.source_id.strip():
            raise Refused("REFUSED[EMPTY_SOURCE_IDENTITY]")
        if self.artifact_digest and (
            len(self.artifact_digest)!=64 or any(c not in "0123456789abcdef" for c in self.artifact_digest)
        ):
            raise Refused("REFUSED[INVALID_ARTIFACT_DIGEST]")
    def fingerprints(self):
        values={f"producer:{self.producer}"}
        if self.run_id:
            values.add(f"run:{self.run_id}")
        if self.artifact_digest:
            values.add(f"artifact:{self.artifact_digest}")
        return frozenset(values)
