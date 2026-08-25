from dataclasses import dataclass, asdict
import hashlib, json
from .refusals import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str
    step: int
    belief_generation: int
    selected_candidate: str | None
    standing: str
    actuation_performed: bool = False

    def __post_init__(self):
        if self.actuation_performed:
            raise Refused("REFUSED_REPORTED_ACTUATION")

    def body(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.body().encode()).hexdigest()

def replay(receipt: Receipt, digest: str) -> bool:
    return not receipt.actuation_performed and receipt.digest() == digest
