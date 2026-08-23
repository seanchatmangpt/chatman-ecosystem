from dataclasses import dataclass
from datetime import datetime
from .selector import Selector,SelectorIdentity
from .subject import Subject,Refused
from .decision import Decision
from .relation import Relation

@dataclass(frozen=True)
class ExternalSelectionReceipt:
    repo: str
    sha: str
    semantic_digest: str
    selector: str
    generation: int
    policy_digest: str
    decision_id: str
    chosen: tuple[str,...]
    candidates: tuple[str,...]
    predicted_error_ppm: int
    evaluation_cost_micros: int
    decided_at: datetime
    authority: str
    actuation_performed: bool

def adapt_external(receipt):
    if receipt.authority not in {"SELECT","OBSERVE|SELECT|CONSTRUCT|VERIFY"}:
        raise Refused("REFUSED[UNEXPECTED_SOURCE_AUTHORITY]")
    if receipt.actuation_performed:
        raise Refused("REFUSED[SOURCE_RECEIPT_REPORTED_ACTUATION]")
    subject=Subject(receipt.repo,receipt.sha,receipt.semantic_digest)
    identity=SelectorIdentity(Selector(receipt.selector),receipt.generation,receipt.policy_digest)
    return Decision(subject,identity,receipt.decision_id,tuple(Relation(x) for x in receipt.chosen),tuple(Relation(x) for x in receipt.candidates),receipt.predicted_error_ppm,receipt.evaluation_cost_micros,receipt.decided_at)
