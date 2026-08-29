from dataclasses import dataclass
from enum import Enum
from .refusal import require

class ActionClass(str, Enum):
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"

@dataclass(frozen=True)
class AuthorityEvidence:
    action: ActionClass
    broker: str | None
    receipt_digest: str | None
    actuation_performed: bool

def admit_authority(e: AuthorityEvidence) -> None:
    if e.action is ActionClass.DO:
        require(e.broker == "BRCE", "BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
        require(e.receipt_digest is not None, "DO_RECEIPT_REQUIRED")
        require(e.actuation_performed, "DO_POSTCONDITION_REQUIRED")
    else:
        require(not e.actuation_performed, "AMBIENT_ACTUATION_REFUSED")
