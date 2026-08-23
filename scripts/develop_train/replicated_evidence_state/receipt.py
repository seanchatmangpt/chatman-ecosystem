import hashlib, json
from dataclasses import dataclass

@dataclass(frozen=True)
class Receipt:
    subject: str
    generation: int
    value_digest: str
    merkle_root: str
    standing: str
    actuation_performed: bool = False

    def body(self):
        return {"schema":"chatman.develop-replicated-evidence-state/1","subject":self.subject,"generation":self.generation,"value_digest":self.value_digest,"merkle_root":self.merkle_root,"standing":self.standing,"actuation_performed":self.actuation_performed}

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()).hexdigest()
