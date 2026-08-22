import hashlib
import json
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class QualificationReceipt:
    schema: str
    subject: str
    frontier_digest: str
    strategy: str
    selected_ids: tuple[str, ...]
    standing: str
    authority: str = "SELECT"
    actuation_performed: bool = False

    @classmethod
    def issue(cls, subject: str, frontier_digest: str, strategy: str, selected_ids: tuple[str, ...], standing: str) -> "QualificationReceipt":
        return cls("chatman.release-evidence-acquisition/1", subject, frontier_digest, strategy, tuple(sorted(selected_ids)), standing)

    def canonical_bytes(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def replay(self, expected_digest: str) -> bool:
        if self.schema != "chatman.release-evidence-acquisition/1":
            return False
        if self.authority != "SELECT" or self.actuation_performed:
            return False
        return self.digest() == expected_digest
